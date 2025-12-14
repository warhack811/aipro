"""
Mami AI - Alembic Migration Environment
=======================================

Bu dosya, Alembic'in veritabanı bağlantısını ve
model metadata'sını yapılandırır.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Proje kök dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Yapılandırma
from app.config import get_settings
from app.core.config_models import (
    APIConfig,
    ImageGenConfig,
    ModelConfig,
    PersonaConfig,
    SystemConfig,
    ThemeConfig,
    UITextConfig,
)
from app.core.models import SQLModel

# Alembic Config
config = context.config

# Python logging yapılandırması
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel metadata (autogenerate için)
target_metadata = SQLModel.metadata

# Veritabanı URL'sini settings'den al
settings = get_settings()
db_url = settings.DATABASE_URL or "sqlite:///data/app.db"
config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """
    Offline modda migration çalıştır.
    
    Bu mod, veritabanına bağlanmadan SQL script'i üretir.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Online modda migration çalıştır.
    
    Veritabanına bağlanarak migration'ları uygular.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite için özel ayarlar
            render_as_batch=True,  # ALTER TABLE desteği için
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

