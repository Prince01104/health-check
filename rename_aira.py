"""Rename the assistant everywhere in the project. Run from the project folder:  python rename_aira.py
Only the display name is changed ("Aira" -> "Profosa", "AIRA" -> "PROFOSA"). Code names such as ui.aira( or tile_aira are lowercase and stay."""
import pathlib

OLD, NEW = "Aira", "Profosa"
SKIP = {".git", "__pycache__", ".pytest_cache", "models", "data"}
EXT = {".py", ".md", ".txt", ".toml", ".json", ".html", ".css", ".csv", ".example"}
changed = 0
for path in pathlib.Path(".").rglob("*"):
    if not path.is_file() or any(p in SKIP for p in path.parts) or (path.suffix not in EXT and path.name != ".gitignore"):
        continue
    if path.name == "rename_aira.py":
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    new = text.replace(OLD, NEW).replace(OLD.upper(), NEW.upper())
    if new != text:
        path.write_text(new, encoding="utf-8")
        changed += 1
        print("updated", path)
print(f"done: {changed} files changed")
