"""
Mami AI - Veritabanı Yönetimi
=============================

Bu modül, uygulamanın veritabanı bağlantılarını yönetir:
- SQLite: Ana ilişkisel veritabanı (kullanıcılar, sohbetler, mesajlar)
- ChromaDB: Vektör veritabanı (semantik hafıza, RAG dokümanları)

Kullanım:
    from app.core.database import get_session, get_chroma_client

    # SQLite oturumu
    with get_session() as session:
        user = session.get(User, user_id)

    # ChromaDB istemcisi
    client = get_chroma_client()
    collection = client.get_collection("memories")

Mimari:
    - Singleton pattern ile tek bir engine/client örneği
    - Lazy loading (ilk kullanımda başlatma)
    - Context manager ile otomatik kaynak yönetimi
"""

import logging

# -----------------------------------------------------------------------------
# ChromaDB TELEMETRY KAPATMA (import ÖNCESİ)
# -----------------------------------------------------------------------------
# ChromaDB telemetry modülü import anında aktif oluyor. Log spam ve
# "capture() takes 1 positional argument but 3 were given" hatalarını önlemek
# için telemetry'yi import öncesi kapatıyoruz.
import os
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Generator, Optional

from sqlalchemy import Engine, event

# SQLModel ve SQLAlchemy imports
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_IMPLEMENTATION", "none")

# ChromaDB imports - opsiyonel bağımlılık
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMADB_AVAILABLE = True
    if TYPE_CHECKING:
        from chromadb import PersistentClient
except ImportError as e:
    chromadb = None
    ChromaSettings = None
    CHROMADB_AVAILABLE = False
    if TYPE_CHECKING:
        PersistentClient = object  # type: ignore

# Modül logger'ı
logger = logging.getLogger(__name__)

# =============================================================================
# GLOBAL DEĞİŞKENLER (SINGLETON INSTANCES)
# =============================================================================
_engine: Optional[Engine] = None
_chroma_client: Optional[object] = None

# =============================================================================
# YAPILANDIRMA YARDIMCILARI
# =============================================================================


def _get_settings():
    """
    Ayarları güvenli şekilde yükler.

    Import döngüsünü önlemek için lazy loading kullanılır.

    Returns:
        Settings veya None: Yapılandırma nesnesi
    """
    try:
        from app.config import get_settings

        return get_settings()
    except ImportError:
        # Eski import yolu (geçiş dönemi uyumluluğu)
        try:
            from app.config import get_settings

            return get_settings()
        except ImportError:
            logger.warning("[DB] Config yüklenemedi, varsayılan değerler kullanılacak")
            return None


def get_db_url() -> str:
    """
    Veritabanı bağlantı URL'sini döndürür.

    Öncelik sırası:
    1. DATABASE_URL ortam değişkeni
    2. Varsayılan SQLite yolu (data/app.db)

    Returns:
        str: Veritabanı bağlantı URL'si

    Example:
        >>> url = get_db_url()
        >>> print(url)
        sqlite:///data/app.db
    """
    settings = _get_settings()

    # Ayarlardan DATABASE_URL varsa kullan
    if settings and settings.DATABASE_URL:
        return settings.DATABASE_URL

    # Varsayılan: Yerel SQLite veritabanı
    base_dir = Path("data")
    base_dir.mkdir(exist_ok=True)
    return f"sqlite:///{base_dir / 'app.db'}"


# =============================================================================
# SQLITE VERITABANI
# =============================================================================


def _init_sqlite_engine() -> Engine:
    """
    SQLite engine'i oluşturur ve yapılandırır.

    Yapılandırma:
    - WAL modu: Yazma performansı için Write-Ahead Logging
    - Foreign keys: Referans bütünlüğü kontrolü
    - check_same_thread=False: FastAPI async uyumluluğu
    - StaticPool: SQLite için optimal connection pooling
    - busy_timeout: "database is locked" hatasını önler

    Returns:
        Engine: SQLAlchemy engine nesnesi
    """
    from sqlalchemy import pool

    db_url = get_db_url()

    engine = create_engine(
        db_url,
        # Connection pool settings for SQLite
        poolclass=pool.StaticPool,  # Single connection pool for SQLite
        connect_args={
            "check_same_thread": False,  # FastAPI async support
            "timeout": 30.0,  # 30 second lock timeout
        },
        # Performance settings
        echo=False,  # Disable SQL logging in production
    )

    # SQLite PRAGMA ayarları (her bağlantıda çalışır)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _connection_record):
        """Her yeni bağlantıda SQLite optimizasyonlarını uygula."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # Performans: Write-Ahead Logging
        cursor.execute("PRAGMA foreign_keys=ON")  # Bütünlük: Foreign key kontrolü
        cursor.execute("PRAGMA busy_timeout=30000")  # 30s lock timeout (milliseconds)
        cursor.execute("PRAGMA synchronous=NORMAL")  # Performance vs safety balance
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.close()

    logger.info(f"[DB] SQLite engine başlatıldı (StaticPool + optimizations): {db_url}")
    return engine


def get_engine() -> Engine:
    """
    Global SQLite engine'i döndürür (Singleton).

    İlk çağrıda engine oluşturulur, sonraki çağrılarda
    aynı instance döndürülür.

    Returns:
        Engine: SQLAlchemy engine nesnesi
    """
    global _engine
    if _engine is None:
        _engine = _init_sqlite_engine()
    return _engine


def create_db_and_tables() -> None:
    """
    Tüm SQLModel tablolarını veritabanında oluşturur.

    ⚠️ DEPRECATED: Bu fonksiyon sadece ilk kurulum için kullanılmalıdır.
    Production'da Alembic migration kullanın!

    Not: init_database_with_defaults() artık önce Alembic'i deniyor,
         bu fonksiyon sadece fallback olarak çalışır.
    """
    logger.warning("[DB] ⚠️  CREATE ALL kullanılıyor - Production'da migration kullanın!")
    # Tüm modelleri import et (tablo tanınması için)
    # Ana modeller
    # Dinamik config modelleri
    from app.core.config_models import (  # noqa: F401
        APIConfig,
        ImageGenConfig,
        ModelConfig,
        PersonaConfig,
        SystemConfig,
        ThemeConfig,
        UITextConfig,
    )
    from app.core.models import (  # noqa: F401
        AIIdentityConfig,
        AnswerCache,
        Conversation,
        ConversationSummary,
        ConversationSummarySettings,
        Feedback,
        Invite,
        Message,
        ModelPreset,
        Session,
        UsageCounter,
        User,
        UserPreference,
    )

    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    logger.info("[DB] Tablolar oluşturuldu/kontrol edildi")


def init_database_with_defaults() -> None:
    """
    Veritabanını başlatır ve migration'ları uygular.

    Uygulama başlangıcında çağrılmalıdır.
    İşlem sırası:
    1. Alembic migration'ları uygula (varsa)
    2. Fallback: İlk kurulum için create_all
    3. Varsayılan config'leri yükle
    """
    # 1. Alembic migration'ları uygula
    migration_success = False
    try:
        import os

        from alembic import command
        from alembic.config import Config

        # alembic.ini var mı kontrol et
        alembic_ini = "alembic.ini"
        if os.path.exists(alembic_ini):
            logger.info("[DB] Alembic migration'ları kontrol ediliyor...")

            alembic_cfg = Config(alembic_ini)

            # Migration'ları otomatik uygula
            command.upgrade(alembic_cfg, "head")
            logger.info("[DB] ✓ Alembic migrations başarıyla uygulandı")
            migration_success = True
        else:
            logger.warning("[DB] alembic.ini bulunamadı, create_all fallback kullanılacak")

    except Exception as e:
        logger.warning(f"[DB] Alembic migration hatası: {e}")
        logger.warning("[DB] Fallback olarak create_all kullanılıyor")

    # 2. Fallback: İlk kurulum veya migration hatası durumunda
    if not migration_success:
        logger.info("[DB] CREATE ALL ile tablolar oluşturuluyor (ilk kurulum)")
        create_db_and_tables()

    # 3. Varsayılan config'leri yükle
    try:
        from app.core.config_seed import seed_all_configs

        results = seed_all_configs(force=False)

        total = sum(results.values())
        if total > 0:
            logger.info(f"[DB] {total} varsayılan config yüklendi: {results}")
    except Exception as e:
        logger.warning(f"[DB] Config seed hatası (ilk kurulumda normal): {e}")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Veritabanı oturumu sağlayan context manager.

    Kullanım:
        with get_session() as session:
            user = session.get(User, 1)
            session.add(new_item)
            session.commit()

    Yields:
        Session: SQLModel veritabanı oturumu

    Note:
        Context manager çıkışında oturum otomatik kapatılır.
        Hata durumunda değişiklikler geri alınır.
    """
    engine = get_engine()
    with Session(engine) as session:
        yield session


# =============================================================================
# CHROMADB VEKTÖR VERİTABANI
# =============================================================================


def get_chroma_persist_dir() -> str:
    """
    ChromaDB veri dizinini döndürür.

    Returns:
        str: ChromaDB kalıcı depolama dizini
    """
    settings = _get_settings()

    if settings and settings.CHROMA_PERSIST_DIR:
        return settings.CHROMA_PERSIST_DIR

    return str(Path("data") / "chroma_db")


def get_chroma_client():
    """
    ChromaDB istemcisini döndürür (Singleton).

    İlk çağrıda PersistentClient oluşturulur, sonraki
    çağrılarda aynı instance döndürülür.

    Returns:
        chromadb.PersistentClient: ChromaDB istemcisi

    Raises:
        ImportError: ChromaDB kütüphanesi yüklü değilse
        Exception: ChromaDB başlatma hatası
    """
    global _chroma_client

    if not CHROMADB_AVAILABLE:
        raise ImportError("chromadb kütüphanesi yüklü değil! " "Yüklemek için: pip install chromadb")

    if _chroma_client is None:
        persist_dir = get_chroma_persist_dir()
        logger.info(f"[DB] ChromaDB başlatılıyor: {persist_dir}")

        try:
            # Telemetry'yi kapat (log spam'ini önlemek için)
            # Environment variable ile telemetry'yi kapat
            import os

            os.environ["ANONYMIZED_TELEMETRY"] = "False"

            if ChromaSettings:
                settings = ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
                _chroma_client = chromadb.PersistentClient(path=persist_dir, settings=settings)  # type: ignore[attr-defined]
            else:
                _chroma_client = chromadb.PersistentClient(path=persist_dir)  # type: ignore[attr-defined]
            logger.info("[DB] ChromaDB başarıyla başlatıldı")
        except Exception as e:
            logger.error(f"[DB] ChromaDB başlatma hatası: {e}")
            raise

    return _chroma_client


def get_memories_collection():
    """
    Hafıza koleksiyonunu döndürür.

    Bu koleksiyon, kullanıcıların uzun vadeli hafızalarını
    (tercihler, kişisel bilgiler) semantik olarak depolar.

    Returns:
        chromadb.Collection: 'memories' koleksiyonu

    Koleksiyon Özellikleri:
        - Cosine benzerlik metrisi
        - Embedding'ler ChromaDB tarafından otomatik oluşturulur
    """
    client = get_chroma_client()
    return client.get_or_create_collection(  # type: ignore[attr-defined]
        name="memories", metadata={"hnsw:space": "cosine"}
    )


def get_rag_collection():
    """
    RAG doküman koleksiyonunu döndürür.

    Bu koleksiyon, kullanıcıların yüklediği dokümanları
    (PDF, TXT) semantik arama için depolar.

    Returns:
        chromadb.Collection: 'rag_docs' koleksiyonu

    Koleksiyon Özellikleri:
        - Cosine benzerlik metriki
        - Chunk'lanmış dokümanlar
    """
    client = get_chroma_client()
    return client.get_or_create_collection(  # type: ignore[attr-defined]
        name="rag_docs", metadata={"hnsw:space": "cosine"}
    )
