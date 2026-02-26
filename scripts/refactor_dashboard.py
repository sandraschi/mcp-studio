import re
from pathlib import Path


def refactor_dashboard():
    source_file = Path("studio_dashboard.py")

    with open(source_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    content = "".join(lines)

    # 1. Update imports
    old_import = (
        "from fastapi import FastAPI, HTTPException, Request  # type: ignore[import-untyped]"
    )
    new_import = "from fastapi import FastAPI, HTTPException, Request  # type: ignore[import-untyped]\nfrom fastapi.templating import Jinja2Templates  # type: ignore[import-untyped]"
    content = content.replace(old_import, new_import)

    # 2. Add templates initialization
    old_app_init = 'app = FastAPI(title="MCP Studio", version=VERSION)\napp.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])'
    new_app_init = (
        old_app_init
        + '\n\n# Templates configuration\ntemplates = Jinja2Templates(directory="mcp_studio/templates")'
    )
    content = content.replace(old_app_init, new_app_init)

    # 3. Replace dashboard function
    # The function starts at 2724 and ends at 5688 approximately.
    # We use regex to find the whole function block.
    # It starts with @app.get("/", response_class=HTMLResponse)
    # and ends with </html>'''

    pattern = re.compile(
        r'@app\.get\("/", response_class=HTMLResponse\)\nasync def dashboard\(\):\n    """Serve the unified MCP Studio dashboard\."""\n    return f\'\'\'(.*?)\'\'\'',
        re.DOTALL,
    )

    new_dashboard_func = """@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    \"\"\"Serve the unified MCP Studio dashboard.\"\"\"
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "version": VERSION, "repos_dir": str(REPOS_DIR)}
    )"""

    content, count = pattern.subn(new_dashboard_func, content)
    print(f"Replaced {count} occurrences of the dashboard function")

    if count == 0:
        # Try a slightly different match if first one failed (e.g. whitespace)
        print("Retrying with flexible regex...")
        pattern = re.compile(
            r'@app\.get\("/", response_class=HTMLResponse\)\s+async def dashboard\(\):\s+""".*?"""\s+return f\'\'\'.*?\'\'\'',
            re.DOTALL,
        )
        content, count = pattern.subn(new_dashboard_func, content)
        print(f"Replaced {count} occurrences with flexible regex")

    if count > 0:
        # Create backup just in case
        backup = source_file.with_suffix(".py.bak2")
        source_file.rename(backup)
        print(f"Created backup at {backup}")

        with open(source_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Successfully refactored {source_file}")
    else:
        print("Failed to replace dashboard function. No changes made.")


if __name__ == "__main__":
    refactor_dashboard()
