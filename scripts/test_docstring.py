import re

content = open('D:/Dev/repos/obsidianmcp/src/obsidian_mcp/server.py').read()

# Original pattern - too strict
pattern = re.compile(
    r'@(?:app|mcp|self\.(?:app|mcp)|server)\.tool.*?\n\s*(?:async\s+)?def\s+\w+[^:]+:\s*\n\s*"""[\s\S]*?(?:Args:|Returns:|Examples:)[\s\S]*?"""',
    re.MULTILINE
)
matches = pattern.findall(content)
print(f'Original pattern: {len(matches)} matches')

# Better pattern - allow return type annotation
pattern2 = re.compile(
    r'@(?:app|mcp|self\.(?:app|mcp)|server)\.tool\(\)\s*\n(?:async\s+)?def\s+\w+\([^)]*\)[^:]*:\s*\n\s*"""[\s\S]*?(?:Args:|Returns:|Examples:)[\s\S]*?"""',
    re.MULTILINE
)
matches2 = pattern2.findall(content)
print(f'Better pattern: {len(matches2)} matches')

# Simple check - just count tools with Args/Returns in docstrings
tools = re.findall(r'@mcp\.tool\(\)', content)
print(f'Total tools: {len(tools)}')
args_sections = re.findall(r'Args:\s*\n', content)
print(f'Args sections: {len(args_sections)}')

