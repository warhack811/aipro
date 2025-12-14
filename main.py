"""
Mami AI - Ana Giriş Noktası
===========================

Bu dosya, backward compatibility için korunmuştur.
Uygulama artık app.main modülünden çalışır.

Çalıştırma (her iki yol da geçerli):
    uvicorn main:app --reload
    uvicorn app.main:app --reload
"""

# =============================================================================
# YENİ YAPIYI KULLAN
# =============================================================================

# Opsiyonel: Diğer export'lar
# app.main'den app nesnesini doğrudan import et
from app.main import (
    app,
    logger,
    settings,
)

# WebSocket bağlantıları için
from app.websocket_sender import connected as connected_clients

# =============================================================================
# NOT: Bu dosya artık sadece bir köprü (bridge) görevi görüyor.
# Tüm gerçek kod app/main.py içinde.
# =============================================================================
