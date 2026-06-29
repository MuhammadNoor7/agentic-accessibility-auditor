import os
import shutil

# Base paths (adjust if needed)
PROJECT_ROOT = r"d:/internship/agentic-accessibility-auditor"
SCREENSHOT_ROOT = os.path.join(PROJECT_ROOT, "data", "screenshots")
# JSON files are stored under MASC_Json/MASC_Json/Full/<Category>
JSON_SOURCE_ROOT = r"d:/internship/archive (2)/MASC_Json/MASC_Json/Full"
DEST_JSON_ROOT = os.path.join(PROJECT_ROOT, "data", "json")

# Ensure destination root exists
os.makedirs(DEST_JSON_ROOT, exist_ok=True)

# Mapping from screenshot category (lowercase) to archive subfolder name
CATEGORY_MAP ={
    "chat": "Chat",
    "home": "Home",
    "list": "List",
    "login": "Login",
    "maps": "Map",
    "menu": "Menu",
    "profile": "Profile",
    "settings": "Setting",
    "welcome": "Welcome",
    "search": "Search"
}

categories = list(CATEGORY_MAP.keys())

# Keep track of which JSON files were successfully copied
copied_jsons = set()

for cat in categories:
    screenshot_dir = os.path.join(SCREENSHOT_ROOT, cat)
    if not os.path.isdir(screenshot_dir):
        print(f"[WARN] Screenshot folder missing: {cat}")
        continue
    json_dir = os.path.join(JSON_SOURCE_ROOT, CATEGORY_MAP[cat])
    if not os.path.isdir(json_dir):
        print(f"[WARN] JSON source folder missing: {json_dir}")
        continue
    dest_dir = os.path.join(DEST_JSON_ROOT, cat)
    os.makedirs(dest_dir, exist_ok=True)

    # Build set of screenshot base names
    screenshot_basenames = {
        os.path.splitext(f)[0]
        for f in os.listdir(screenshot_dir)
        if f.lower().endswith('.jpg')
    }

    for base in screenshot_basenames:
        src_json_path = os.path.join(json_dir, f"{base}.json")
        if os.path.isfile(src_json_path):
            shutil.copy2(src_json_path, dest_dir)
            copied_jsons.add(os.path.join(cat, f"{base}.json"))
        else:
            print(f"[INFO] No JSON found for screenshot {base}.jpg in category {cat}")

print(f"Done. Copied {len(copied_jsons)} JSON files to {DEST_JSON_ROOT}.")
