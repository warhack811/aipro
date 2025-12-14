# -*- coding: utf-8 -*-
"""
Mami AI - Image Router Tests
============================

Bu modul, image routing sisteminin testlerini icerir.

Test Kategorileri:
    1. NSFW Detection
    2. Checkpoint Selection
    3. Permission Enforcement
    4. Policy Blocking

Calistirma:
    pytest tests/test_image_router.py -v
"""

import pytest
import sys
import os

# Proje rootunu path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TEST 1: CHECKPOINT SELECTION
# =============================================================================

class TestCheckpointSelection:
    """Checkpoint secimi testleri."""
    
    @pytest.fixture
    def user_with_nsfw_permission(self):
        """NSFW izni olan kullanici."""
        class MockUser:
            id = 1
            username = "test_user"
            role = "member"
            is_banned = False
            bela_unlocked = False
            permissions = {
                "can_use_image": True,
                "censorship_level": 0,  # UNRESTRICTED
            }
        return MockUser()
    
    @pytest.fixture
    def user_without_nsfw_permission(self):
        """NSFW izni olmayan kullanici."""
        class MockUser:
            id = 2
            username = "test_user2"
            role = "member"
            is_banned = False
            bela_unlocked = False
            permissions = {
                "can_use_image": True,
                "censorship_level": 1,  # NORMAL
            }
        return MockUser()
    
    @pytest.fixture
    def admin_user(self):
        """Admin kullanici."""
        class MockUser:
            id = 3
            username = "admin"
            role = "admin"
            is_banned = False
            permissions = {}
        return MockUser()
    
    def test_safe_content_uses_standard_checkpoint(self, user_with_nsfw_permission):
        """Guvenli icerik standard checkpoint kullanmali."""
        from app.image.routing import decide_image_job, FluxVariant, CHECKPOINTS
        
        spec = decide_image_job("a cute cat", user_with_nsfw_permission)
        
        assert spec.variant == FluxVariant.STANDARD
        assert spec.checkpoint_name == CHECKPOINTS[FluxVariant.STANDARD]
        assert spec.checkpoint_name == "flux1-dev-bnb-nf4-v2.safetensors"
        assert spec.blocked is False
        assert "safe_content_using_standard" in spec.reasons
    
    def test_nsfw_content_with_permission_uses_uncensored(self, user_with_nsfw_permission):
        """NSFW icerik + izin var -> uncensored checkpoint."""
        from app.image.routing import decide_image_job, FluxVariant, CHECKPOINTS
        
        spec = decide_image_job("nude woman", user_with_nsfw_permission)
        
        assert spec.variant == FluxVariant.UNCENSORED
        assert spec.checkpoint_name == CHECKPOINTS[FluxVariant.UNCENSORED]
        assert spec.checkpoint_name == "fluxedUpFluxNSFW_51FP8.safetensors"
        assert spec.blocked is False
        assert spec.flags["nsfw_detected"] is True
        assert "nsfw_allowed_using_uncensored" in spec.reasons
    
    def test_nsfw_content_without_permission_blocked(self, user_without_nsfw_permission):
        """NSFW icerik + izin yok -> 403."""
        from app.image.routing import decide_image_job
        
        spec = decide_image_job("nude woman", user_without_nsfw_permission)
        
        assert spec.blocked is True
        assert spec.block_reason is not None
        assert "izniniz bulunmuyor" in spec.block_reason.lower()
        assert spec.flags["nsfw_detected"] is True
        assert "nsfw_blocked_no_permission" in spec.reasons
    
    def test_admin_can_generate_nsfw(self, admin_user):
        """Admin kullanici NSFW uretebilir."""
        from app.image.routing import decide_image_job, FluxVariant
        
        spec = decide_image_job("nude woman", admin_user)
        
        assert spec.variant == FluxVariant.UNCENSORED
        assert spec.blocked is False
        assert spec.flags["nsfw_detected"] is True


# =============================================================================
# TEST 2: NSFW DETECTION
# =============================================================================

class TestNSFWDetection:
    """NSFW tespit testleri."""
    
    @pytest.fixture
    def safe_user(self):
        """NSFW izni olan kullanici."""
        class MockUser:
            id = 1
            username = "test_user"
            role = "member"
            is_banned = False
            permissions = {
                "can_use_image": True,
                "censorship_level": 0,
            }
        return MockUser()
    
    def test_nsfw_keywords_detected(self, safe_user):
        """NSFW kelimeler tespit edilmeli."""
        from app.image.routing import decide_image_job
        
        nsfw_prompts = [
            "nude woman",
            "naked man",
            "çıplak kadın",
            "seksi kız",
            "erotic scene",
            "18+ content",
            "xxx image",
        ]
        
        for prompt in nsfw_prompts:
            spec = decide_image_job(prompt, safe_user)
            assert spec.flags["nsfw_detected"] is True, f"Failed for: {prompt}"
    
    def test_safe_keywords_not_detected(self, safe_user):
        """Guvenli kelimeler NSFW olarak tespit edilmemeli."""
        from app.image.routing import decide_image_job
        
        safe_prompts = [
            "a cute cat",
            "beautiful landscape",
            "sunset over mountains",
            "portrait of a person",
            "abstract art",
        ]
        
        for prompt in safe_prompts:
            spec = decide_image_job(prompt, safe_user)
            assert spec.flags["nsfw_detected"] is False, f"Failed for: {prompt}"


# =============================================================================
# TEST 3: PERMISSION ENFORCEMENT
# =============================================================================

class TestPermissionEnforcement:
    """Izin zorlama testleri."""
    
    @pytest.fixture
    def user_no_image_permission(self):
        """Gorsel uretim izni olmayan kullanici."""
        class MockUser:
            id = 1
            username = "test_user"
            role = "member"
            is_banned = False
            permissions = {
                "can_use_image": False,
            }
        return MockUser()
    
    @pytest.fixture
    def banned_user(self):
        """Yasakli kullanici."""
        class MockUser:
            id = 2
            username = "banned_user"
            role = "member"
            is_banned = True
            permissions = {}
        return MockUser()
    
    def test_no_image_permission_blocked(self, user_no_image_permission):
        """Gorsel uretim izni olmayan kullanici reddedilmeli."""
        from app.image.routing import decide_image_job
        
        spec = decide_image_job("a cute cat", user_no_image_permission)
        
        assert spec.blocked is True
        assert "izniniz bulunmuyor" in spec.block_reason.lower()
        assert "no_image_permission" in spec.reasons
    
    def test_banned_user_blocked(self, banned_user):
        """Yasakli kullanici reddedilmeli."""
        from app.image.routing import decide_image_job
        
        spec = decide_image_job("a cute cat", banned_user)
        
        assert spec.blocked is True


# =============================================================================
# TEST 4: PARAMETERS
# =============================================================================

class TestParameters:
    """Parametre testleri."""
    
    @pytest.fixture
    def safe_user(self):
        """Guvenli kullanici."""
        class MockUser:
            id = 1
            username = "test_user"
            role = "member"
            is_banned = False
            permissions = {
                "can_use_image": True,
            }
        return MockUser()
    
    def test_default_parameters(self, safe_user):
        """Varsayilan parametreler uygulanmali."""
        from app.image.routing import decide_image_job
        
        spec = decide_image_job("a cute cat", safe_user)
        
        assert spec.params["steps"] == 20
        assert spec.params["width"] == 1024
        assert spec.params["height"] == 1024
        assert spec.params["cfg_scale"] == 1.0
        assert spec.params["sampler_name"] == "Euler"
        assert spec.params["scheduler"] == "Simple"
    
    def test_custom_parameters(self, safe_user):
        """Ozel parametreler korunmali."""
        from app.image.routing import decide_image_job
        
        custom_params = {
            "steps": 30,
            "width": 512,
            "height": 512,
        }
        
        spec = decide_image_job("a cute cat", safe_user, params=custom_params)
        
        assert spec.params["steps"] == 30
        assert spec.params["width"] == 512
        assert spec.params["height"] == 512
    
    def test_negative_prompt(self, safe_user):
        """Negative prompt kullanilmali."""
        from app.image.routing import decide_image_job
        
        spec = decide_image_job(
            "a cute cat",
            safe_user,
            negative_prompt="ugly, blurry"
        )
        
        assert spec.negative_prompt == "ugly, blurry"


# =============================================================================
# TEST 5: SPEC TO DICT
# =============================================================================

class TestSpecToDict:
    """Spec to dict testleri."""
    
    @pytest.fixture
    def safe_user(self):
        """Guvenli kullanici."""
        class MockUser:
            id = 1
            username = "test_user"
            role = "member"
            is_banned = False
            permissions = {
                "can_use_image": True,
            }
        return MockUser()
    
    def test_to_dict_conversion(self, safe_user):
        """to_dict() dogru cevirmeli."""
        from app.image.routing import decide_image_job
        
        spec = decide_image_job("a cute cat", safe_user)
        spec_dict = spec.to_dict()
        
        assert "variant" in spec_dict
        assert "checkpoint_name" in spec_dict
        assert "prompt" in spec_dict
        assert "flags" in spec_dict
        assert "reasons" in spec_dict
        assert "blocked" in spec_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])







