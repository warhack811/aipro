"""
Mami AI - Pytest Yapılandırması
===============================

Test fixture'ları ve ortak yapılandırma.
"""

import os
import sys
from pathlib import Path

import pytest

# Proje kök dizinini Python path'e ekle
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def app_settings():
    """Test için uygulama ayarlarını döndürür."""
    from app.config import get_settings

    return get_settings()


@pytest.fixture(scope="session")
def test_client():
    """
    FastAPI test client'ı.

    Kullanım:
        def test_health(test_client):
            response = test_client.get("/health")
            assert response.status_code == 200
    """
    from fastapi.testclient import TestClient

    from main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_user_message():
    """Test için örnek kullanıcı mesajı."""
    return "Merhaba, nasılsın?"


@pytest.fixture
def sample_code_message():
    """Test için kod içeren mesaj."""
    return "Python'da liste oluşturma:\n```python\nmy_list = [1, 2, 3]\n```"
