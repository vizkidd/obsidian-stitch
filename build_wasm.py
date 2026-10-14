import os
import shutil

DIST_DIR = "dist"

def build():
    print("Building WASM Static Site for GitHub Pages...")
    
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    os.makedirs(DIST_DIR, exist_ok=True)

    # Copy core WASM index file
    if os.path.exists("index.html"):
        shutil.copy("index.html", os.path.join(DIST_DIR, "index.html"))
        print("✓ Copied index.html to dist/")

    # Copy optional static assets if directory exists
    if os.path.exists("static"):
        shutil.copytree("static", os.path.join(DIST_DIR, "static"))
        print("✓ Copied static/ directory to dist/")

    print("Build complete! Output directory: dist/")

if __name__ == "__main__":
    build()