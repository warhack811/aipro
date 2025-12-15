
import os
import ast
import re

REPO_ROOT = "."
OUTPUT_FILE = "docs/auto/api_routes.md"

def get_router_prefixes(main_path):
    prefixes = {}
    try:
        with open(main_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "include_router":
                    if node.args:
                        if isinstance(node.args[0], ast.Attribute) and isinstance(node.args[0].value, ast.Name):
                            prefixes[node.args[0].value.id] = "" # placeholder
                            for kw in node.keywords:
                                if kw.arg == "prefix" and isinstance(kw.value, (ast.Str, ast.Constant)):
                                    val = kw.value.value if isinstance(kw.value, ast.Constant) else kw.value.s
                                    prefixes[node.args[0].value.id] = val
                        elif isinstance(node.args[0], ast.Name): # router variable directly
                             prefixes[node.args[0].id] = ""
                             for kw in node.keywords:
                                if kw.arg == "prefix" and isinstance(kw.value, (ast.Str, ast.Constant)):
                                    val = kw.value.value if isinstance(kw.value, ast.Constant) else kw.value.s
                                    prefixes[node.args[0].id] = val
    except:
        pass
    return prefixes

def extract_routes(filepath, known_prefixes):
    routes = []
    fname = os.path.basename(filepath)
    mod = fname.replace(".py", "")
    prefix = known_prefixes.get(mod, "")
    
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
        tree = ast.parse(content)
    except:
        return []

    router_names = {"router", "app"}
    
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                     if dec.func.attr in ["get", "post", "put", "delete", "options", "head", "patch", "websocket"]:
                         # Check if router name matches
                         rname = ""
                         if isinstance(dec.func.value, ast.Name):
                             rname = dec.func.value.id
                         
                         if rname in router_names:
                             path = ""
                             if dec.args and isinstance(dec.args[0], (ast.Str, ast.Constant)):
                                 path = dec.args[0].value if isinstance(dec.args[0], ast.Constant) else dec.args[0].s
                             
                             full_path = f"{prefix}{path}".replace("//", "/")
                             method = dec.func.attr.upper()
                             
                             routes.append({
                                 "method": method,
                                 "path": full_path,
                                 "handler": f"{mod}:{node.name}",
                                 "auth": "Required" if "Depends" in ast.dump(node.args) else "None",
                                 "side_effects": "-"
                             })
    return routes

def main():
    prefixes = get_router_prefixes("app/main.py")
    all_routes = []
    for root, dirs, files in os.walk("app"):
        for f in files:
            if f.endswith(".py"):
                all_routes.extend(extract_routes(os.path.join(root, f), prefixes))
    
    all_routes.sort(key=lambda x: (x["path"], x["method"]))
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# API Routes\n\n| Method | Path | Handler | Auth |\n|---|---|---|---|\n")
        for r in all_routes:
            f.write(f"| {r['method']} | {r['path']} | `{r['handler']}` | {r['auth']} |\n")
    print(f"Generated {len(all_routes)} routes")

if __name__ == "__main__":
    main()
