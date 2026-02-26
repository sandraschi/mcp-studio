import re
import os
from pathlib import Path


def extract_template():
    source_file = Path("studio_dashboard.py")
    target_dir = Path("templates")
    target_dir.mkdir(exist_ok=True)
    target_file = target_dir / "dashboard.html"

    with open(source_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the f-string content
    # Look for: return f''' ... '''
    match = re.search(r"return f'''(.*?)'''", content, re.DOTALL)
    if not match:
        print("Could not find template f-string")
        return

    template_content = match.group(1)

    # Identify variables - we only want to replace actual Python config variables
    # For now, we know specifically these two:
    known_vars = ["VERSION", "REPOS_DIR"]

    # Process content:
    # 1. Unescape double braces: {{ -> {, }} -> }
    # This will correctly turn ${{progress...}} into ${progress...}
    # and tailwind.config = {{ into tailwind.config = {
    processed = template_content.replace("{{", "{").replace("}}", "}")

    # 2. Identify and replace variables - we only want to replace actual Python config variables
    for var in known_vars:
        # Note: the original content had {VERSION}, which became {VERSION} (unchanged by unescape)
        # unless it was {{VERSION}}, which it wasn't.
        processed = processed.replace("{" + var + "}", "{{ " + var.lower() + " }}")

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(processed)

    print(f"Template extracted to {target_file}")


if __name__ == "__main__":
    extract_template()
