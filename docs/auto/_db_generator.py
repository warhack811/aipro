
import os
import ast
import re

REPO_ROOT = "."
OUTPUT_FILE = "docs/auto/db_schema.md"

def extract_models(filepath):
    models = []
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
        tree = ast.parse(content)
    except:
        return []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            is_model = False
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id in ["SQLModel", "Base", "Model"]:
                    is_model = True
            
            # Check for table=True kwarg
            is_table = False
            for kw in node.keywords:
                if kw.arg == "table" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    is_table = True
            
            if is_model: # SQLModel or Base
                fields = []
                for item in node.body:
                    if isinstance(item, ast.AnnAssign):
                        fname = item.target.id if isinstance(item.target, ast.Name) else "?"
                        ftype = ast.get_source_segment(content, item.annotation)
                        fields.append(f"{fname}: {ftype}")
                
                models.append({
                    "name": node.name,
                    "table": is_table,
                    "fields": fields
                })
    return models

def main():
    all_models = []
    for root, dirs, files in os.walk("app"):
        for f in files:
            if f.endswith(".py"):
                all_models.extend(extract_models(os.path.join(root, f)))
    
    # Migrations
    migrations = []
    ver_dir = "alembic/versions"
    if os.path.exists(ver_dir):
        for f in sorted(os.listdir(ver_dir)):
            if f.endswith(".py"):
                migrations.append(f)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# Database Schema\n\n## Models\n")
        for m in all_models:
            if m["table"]:
                f.write(f"### {m['name']}\n")
                f.write("| Column | Type |\n|---|---|\n")
                for field in m["fields"]:
                    col, typ = field.split(":", 1)
                    f.write(f"| {col} | `{typ.strip()}` |\n")
                f.write("\n")
        
        f.write("\n## Migrations\n")
        for mig in migrations:
            f.write(f"- {mig}\n")

    print(f"Generated DB schema with {len(all_models)} models")

if __name__ == "__main__":
    main()
