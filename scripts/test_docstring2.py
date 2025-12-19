import re
from pathlib import Path

# Scanner's pattern - requires @app.tool()
pattern_with_parens = re.compile(
    r'@(?:app|mcp|self\.(?:app|mcp)|server)\.tool\(\)\s*\n(?:async\s+)?def\s+\w+\([^)]*\)[^:]*:\s*\n\s*"""[\s\S]*?(?:Args:|Returns:|Examples:)[\s\S]*?"""',
    re.MULTILINE
)

# Pattern that also matches @app.tool without parens
pattern_no_parens = re.compile(
    r'@(?:app|mcp|self\.(?:app|mcp)|server)\.tool(?:\(\))?\s*\n(?:async\s+)?def\s+\w+\([^)]*\)[^:]*:\s*\n\s*"""[\s\S]*?(?:Args:|Returns:|Examples:)[\s\S]*?"""',
    re.MULTILINE
)

# Test on download_tools.py
content = Path('D:/Dev/repos/blender-mcp/src/blender_mcp/tools/download_tools.py').read_text(encoding='utf-8')
matches1 = pattern_with_parens.findall(content)
matches2 = pattern_no_parens.findall(content)
print(f'download_tools.py: with_parens={len(matches1)}, no_parens={len(matches2)}')

# Test on mesh_tools.py
content2 = Path('D:/Dev/repos/blender-mcp/src/blender_mcp/tools/mesh/mesh_tools.py').read_text(encoding='utf-8')
matches3 = pattern_with_parens.findall(content2)
matches4 = pattern_no_parens.findall(content2)
print(f'mesh_tools.py: with_parens={len(matches3)}, no_parens={len(matches4)}')

# Check decorator styles
decorators = re.findall(r'@app\.tool(?:\(\))?', content)
print(f'download_tools.py decorators: {decorators}')

