"""Hafızaları listele."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.memory_service import MemoryService

ms = MemoryService()
col = ms._get_collection()
result = col.get(include=['metadatas', 'documents'])

print(f"Toplam: {len(result['ids'])} hafiza\n")

for i, (mid, text, meta) in enumerate(zip(result['ids'], result['documents'], result['metadatas'])):
    is_active = meta.get('is_active', True)
    topic = meta.get('topic', '?')
    importance = meta.get('importance', 0.5)
    
    status = "✅" if is_active else "❌"
    print(f"{status} [{i+1}] {text[:100]}")
    print(f"    Kategori: {topic} | Önem: {importance} | ID: {mid[:8]}...")
    print()
