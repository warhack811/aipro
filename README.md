# Mami AI

Kısa açıklama: Mami AI, FastAPI tabanlı bir asistan uygulamasıdır (backend `main.py` ile başlar, dokümanlar `docs/` altında).

## Resmi çalışma yolları
- Make ile: `make format && make lint && make test && make type-check`
- Make yoksa (eşdeğer komutlar):
  - Format: `black .` ve `isort .`
  - Lint: `ruff check .`
  - Test: `pytest -v`
  - Type-check: `mypy app/`

## Developer setup
- Python 3.10+ kullanın, bağımlılıkları kurun: `pip install -r requirements-dev.txt` (veya `make install-dev`).
- Git kancalarını kurun: `pre-commit install`.
- Kancaları manuel çalıştırmak için: `pre-commit run --all-files`.

## Çalıştırma
- Geliştirme sunucusu: `make dev` (hot reload) veya `uvicorn main:app --reload --host 0.0.0.0 --port 8000`.
- Üretim benzeri: `make run` veya `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4`.

## Dokümantasyon
- Detaylı dokümanlar `docs/README.md` altında listelidir.
