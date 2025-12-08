import re
from pathlib import Path

# Test pattern on help_tools.py
content = Path('D:/Dev/repos/blender-mcp/src/blender_mcp/tools/help_tools.py').read_text(encoding='utf-8')

# Count @app.tool decorators
tool_count = len(re.findall(r'@app\.tool', content))
print(f'Tool decorators: {tool_count}')

# Test our pattern - note: needs to handle indented decorators in nested functions
pattern = re.compile(
    r'@(?:app|mcp|self\.(?:app|mcp)|server)\.tool(?:\(\))?\s*\n\s*(?:async\s+)?def\s+\w+\([^)]*\)[^:]*:\s*\n\s*"""[\s\S]*?(?:Args:|Returns:|Examples:)[\s\S]*?"""',
    re.MULTILINE
)
matches = pattern.findall(content)
print(f'Pattern matches: {len(matches)}')

# Show first decorator context
first = content.find('@app.tool')
print(f'\nFirst decorator context:')
print(content[first:first+300])

