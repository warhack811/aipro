# =============================================================================
# Mami AI - Makefile
# =============================================================================
# Yaygın geliştirme görevleri için kısayollar.
#
# Kullanım:
#   make help        - Yardım göster
#   make dev         - Geliştirme sunucusu
#   make test        - Testleri çalıştır
#   make lint        - Kod kontrolü
#   make format      - Kod formatlama
#   make docker      - Docker ile çalıştır
# =============================================================================

.PHONY: help dev run test lint format clean docker db-migrate db-upgrade
PY_TARGETS := app tests main.py alembic scripts
# Varsayılan hedef
.DEFAULT_GOAL := help

# Renkli çıktı
YELLOW := \033[33m
GREEN := \033[32m
RESET := \033[0m

help: ## Bu yardım mesajını göster
	@echo ""
	@echo "Mami AI - Geliştirici Komutları"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ---------------------------------------------------------------------------
# Geliştirme
# ---------------------------------------------------------------------------

dev: ## Geliştirme sunucusunu başlat (hot reload)
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run: ## Production sunucusunu başlat
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

install: ## Bağımlılıkları yükle
	pip install -r requirements.txt

install-dev: ## Geliştirme bağımlılıklarını yükle
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# ---------------------------------------------------------------------------
# Test ve Kalite
# ---------------------------------------------------------------------------

test: ## Testleri çalıştır
	pytest tests/ -v

test-cov: ## Test coverage ile çalıştır
	pytest tests/ -v --cov=app --cov-report=html

lint: ## Kod kalite kontrolü (Ruff)
	ruff check $(PY_TARGETS)

lint-fix: ## Lint hatalarını otomatik düzelt
	ruff check --fix $(PY_TARGETS)

format: ## Kodu formatla (Black + isort)
	black $(PY_TARGETS)
	isort $(PY_TARGETS)

type-check: ## Tip kontrolü (mypy)
	mypy app/

# ---------------------------------------------------------------------------
# Veritabanı
# ---------------------------------------------------------------------------

db-migrate: ## Yeni migration oluştur (msg gerekli)
	@read -p "Migration mesajı: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-upgrade: ## Migration'ları uygula
	alembic upgrade head

db-downgrade: ## Son migration'ı geri al
	alembic downgrade -1

db-history: ## Migration geçmişini göster
	alembic history

db-reset: ## Veritabanını sıfırla (DİKKAT!)
	rm -f data/app.db
	rm -rf data/chroma_db/*
	python -c "from core.database import create_db_and_tables; create_db_and_tables()"

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker: ## Docker ile çalıştır
	docker-compose up

docker-build: ## Docker image oluştur
	docker build -t mami-ai:latest .

docker-prod: ## Production modda Docker
	docker-compose up -d

docker-down: ## Docker'ı durdur
	docker-compose down

docker-logs: ## Docker loglarını göster
	docker-compose logs -f mami-ai

# ---------------------------------------------------------------------------
# Temizlik
# ---------------------------------------------------------------------------

clean: ## Geçici dosyaları temizle
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage 2>/dev/null || true

clean-all: clean ## Tüm geçici dosyaları ve veriyi temizle
	rm -rf data/app.db data/chroma_db/* logs/*.log

