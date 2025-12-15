
import os
import json
import datetime
import ast
import re

IGNORED_DIRS = {'.git', '__pycache__', '.venv', 'node_modules', 'dist', 'build', '.pytest_cache', '.ruff_cache', '.github', '.idea', '.vscode'}
REPO_ROOT = "."
OUTPUT_DIR = "docs/auto"

def is_ignored(path):
    parts = path.split(os.sep)
    for part in parts:
        if part in IGNORED_DIRS:
            return True
    return False

def get_tree_structure(root_dir):
    tree_lines = []
    
    # Simple walk and print
    # But walk is top-down.
    
    # Let's do a recursive function to sort and print nice tree
    def walk_dir(current_path, prefix=""):
        try:
            entries = sorted(os.listdir(current_path))
        except PermissionError:
            return

        # Filter entries
        entries = [e for e in entries if e not in IGNORED_DIRS]
        
        for index, entry in enumerate(entries):
            full_path = os.path.join(current_path, entry)
            is_last = (index == len(entries) - 1)
            
            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{entry}")
            
            if os.path.isdir(full_path):
                extension = "    " if is_last else "│   "
                walk_dir(full_path, prefix + extension)

    tree_lines.append(".")
    walk_dir(root_dir)
    return "\n".join(tree_lines)

def analyze_python_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return {}

    info = {
        "imports": [],
        "exports": [],
        "entrypoints": [],
        "calls_out_to": [],
        "summary": "No summary available."
    }
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return info

    # Docstring
    docstring = ast.get_docstring(tree)
    if docstring:
        info["summary"] = docstring.strip().split('\n')[0] # First line of docstring
    
    # Imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                info["imports"].append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                info["imports"].append(node.module)
    
    # Exports / Definitions
    # Heuristic: top level functions and classes
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            info["exports"].append(f"func:{node.name}")
        elif isinstance(node, ast.ClassDef):
            info["exports"].append(f"class:{node.name}")
            
    # Calls out to (Heuristic keywords in content)
    # entrypoints
    if "FastAPI" in info["imports"] or "fastapi" in info["imports"]:
        if "app = FastAPI" in content or "APIRouter" in content:
            info["entrypoints"].append("fastapi_app")
    
    return info

def analyze_ts_file(path):
    # Simple regex analysis
    info = {
        "imports": [],
        "exports": [],
        "entrypoints": [],
        "calls_out_to": [],
        "summary": "TypeScript/JavaScript file."
    }
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.splitlines()
    except Exception:
        return info
        
    # very basic import regex
    import_matches = re.findall(r'import\s+.*from\s+[\'"](.*)[\'"]', content)
    info["imports"].extend(import_matches)
    
    if "export " in content:
        info["exports"].append("Exports symbols")
        
    return info

def generate_inventory():
    inventory = {
        "generated_at": datetime.datetime.now().isoformat(),
        "repo_root": REPO_ROOT,
        "stats": {
            "total_files": 0,
            "total_python_files": 0,
            "total_ts_files": 0,
            "total_test_files": 0
        },
        "files": []
    }
    
    for root, dirs, fi in os.walk(REPO_ROOT):
        # Modify dirs in-place to skip ignored
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        
        for filename in fi:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, REPO_ROOT)
            
            if is_ignored(rel_path): # Check if file path itself has ignored parts (double check)
                continue
                
            extension = os.path.splitext(filename)[1].lower()
            
            # Count LOC
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    loc = sum(1 for _ in f)
            except:
                loc = 0
            
            file_entry = {
                "path": rel_path.replace("\\", "/"),
                "type": "other",
                "loc": loc,
                "summary": "Standard file.",
                "imports": [],
                "exports": [],
                "entrypoints": [],
                "calls_out_to": [],
                "related_tests": []
            }
            
            inventory["stats"]["total_files"] += 1
            
            if extension == ".py":
                file_entry["type"] = "python"
                inventory["stats"]["total_python_files"] += 1
                py_info = analyze_python_file(filepath)
                file_entry.update(py_info)
                
                if "test" in filename:
                     inventory["stats"]["total_test_files"] += 1
            elif extension in [".ts", ".tsx", ".js", ".jsx"]:
                file_entry["type"] = "typescript" if "ts" in extension else "javascript"
                inventory["stats"]["total_ts_files"] += 1
                ts_info = analyze_ts_file(filepath)
                file_entry.update(ts_info)
            elif extension == ".md":
                file_entry["type"] = "markdown"
            elif extension in [".json", ".yaml", ".yml"]:
                file_entry["type"] = extension[1:]
                
            # Improved Summary Heuristic if default
            if file_entry["summary"] == "Standard file." or file_entry["summary"] == "No summary available.":
                 file_entry["summary"] = f"{file_entry['type']} file validation/logic."
            
            inventory["files"].append(file_entry)
            
    return inventory

def main():
    # 1. Tree
    print("Generating tree...")
    tree_content = get_tree_structure(REPO_ROOT)
    with open(os.path.join(OUTPUT_DIR, "repo_tree.txt"), "w", encoding="utf-8") as f:
        f.write(tree_content)
        
    # 2. Inventory
    print("Generating inventory...")
    inv = generate_inventory()
    with open(os.path.join(OUTPUT_DIR, "repo_inventory.json"), "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2)

if __name__ == "__main__":
    main()
