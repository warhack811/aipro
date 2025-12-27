# -*- coding: utf-8 -*-
"""
Smart Router Test - Basit Test Scripti
======================================
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MockUser:
    """Test icin mock User sinifi."""

    id: int = 1
    username: str = "test_user"
    bela_unlocked: bool = False
    is_banned: bool = False
    selected_model: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = {}


def run_tests():
    """Tum test senaryolarini calistirir."""
    from app.chat.smart_router import RoutingTarget, SmartRouter, ToolIntent

    router = SmartRouter()
    results = []

    print("=" * 60)
    print("SMART ROUTER TEST SENARYOLARI")
    print("=" * 60)

    # TEST 1: resim ciz -> IMAGE
    print("\nTEST 1: 'resim ciz' -> IMAGE")
    user = MockUser(permissions={"can_use_image": True})
    d = router.route(message="bana guzel bir resim ciz", user=user)
    passed = d.target == RoutingTarget.IMAGE
    results.append(("resim_ciz", passed))
    print(f"  Target: {d.target.value}")
    print(f"  Reasons: {d.reason_codes}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")

    # TEST 2: hava durumu -> INTERNET
    print("\nTEST 2: 'hava durumu' -> INTERNET")
    user = MockUser(permissions={"can_use_internet": True})
    d = router.route(message="hava bugun nasil olacak", user=user)
    passed = d.target == RoutingTarget.INTERNET
    results.append(("hava_durumu", passed))
    print(f"  Target: {d.target.value}")
    print(f"  Reasons: {d.reason_codes}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")

    # TEST 3: bela + unlocked -> LOCAL
    print("\nTEST 3: requested_model=bela + bela_unlocked=True -> LOCAL")
    user = MockUser(bela_unlocked=True)
    d = router.route(message="merhaba", user=user, requested_model="bela")
    passed = d.target == RoutingTarget.LOCAL
    results.append(("bela_unlocked", passed))
    print(f"  Target: {d.target.value}")
    print(f"  Reasons: {d.reason_codes}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")

    # TEST 4: bela + locked -> GROQ
    print("\nTEST 4: requested_model=bela + bela_unlocked=False -> GROQ")
    user = MockUser(bela_unlocked=False)
    d = router.route(message="merhaba", user=user, requested_model="bela")
    passed = d.target == RoutingTarget.GROQ
    results.append(("bela_locked", passed))
    print(f"  Target: {d.target.value}")
    print(f"  Reasons: {d.reason_codes}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")

    # TEST 5: strict + nsfw image -> BLOCKED
    print("\nTEST 5: censorship_level=2 + nsfw image -> BLOCKED")
    user = MockUser(permissions={"can_use_image": True, "censorship_level": 2})
    d = router.route(message="nude kadin ciz", user=user)
    passed = d.blocked == True
    results.append(("nsfw_blocked", passed))
    print(f"  Target: {d.target.value}")
    print(f"  Blocked: {d.blocked}")
    print(f"  Reasons: {d.reason_codes}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")

    # TEST 6: unrestricted + nsfw image -> IMAGE
    print("\nTEST 6: censorship_level=0 + nsfw image -> IMAGE (allowed)")
    user = MockUser(permissions={"can_use_image": True, "censorship_level": 0})
    d = router.route(message="nude kadin ciz", user=user)
    passed = d.target == RoutingTarget.IMAGE and not d.blocked
    results.append(("nsfw_allowed", passed))
    print(f"  Target: {d.target.value}")
    print(f"  Blocked: {d.blocked}")
    print(f"  Reasons: {d.reason_codes}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")

    # TEST 7: roleplay -> LOCAL
    print("\nTEST 7: roleplay icerik -> LOCAL")
    user = MockUser(bela_unlocked=True, permissions={"censorship_level": 1})
    d = router.route(message="seninle roleplay yapmak istiyorum", user=user)
    passed = d.target == RoutingTarget.LOCAL
    results.append(("roleplay_local", passed))
    print(f"  Target: {d.target.value}")
    print(f"  Tool Intent: {d.tool_intent.value}")
    print(f"  Reasons: {d.reason_codes}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")

    # TEST 8: normal sohbet -> GROQ
    print("\nTEST 8: normal sohbet -> GROQ")
    user = MockUser(bela_unlocked=True, permissions={"censorship_level": 1})
    d = router.route(message="Python nedir aciklar misin", user=user)
    passed = d.target == RoutingTarget.GROQ
    results.append(("normal_groq", passed))
    print(f"  Target: {d.target.value}")
    print(f"  Reasons: {d.reason_codes}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")

    # OZET
    print("\n" + "=" * 60)
    print("TEST SONUCLARI")
    print("=" * 60)

    total = len(results)
    passed_count = sum(1 for _, p in results if p)

    for name, p in results:
        status = "PASS" if p else "FAIL"
        print(f"  [{status}] {name}")

    print(f"\nToplam: {total}, Gecen: {passed_count}, Kalan: {total - passed_count}")

    if passed_count == total:
        print("\nTUM TESTLER BASARILI!")
        return 0
    else:
        print("\nBAZI TESTLER BASARISIZ!")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
