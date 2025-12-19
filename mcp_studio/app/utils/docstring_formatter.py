"""Docstring formatting utilities for better UI display."""

import re
from typing import Dict, List, Optional, Tuple


def parse_docstring(docstring: str) -> Dict[str, any]:
    """Parse a docstring into structured sections.
    
    Args:
        docstring: The raw docstring text
        
    Returns:
        Dictionary with keys:
        - description: Main description text
        - args: List of (name, type, description) tuples
        - returns: Return description
        - raises: List of (exception, description) tuples
        - examples: List of example strings
        - notes: Additional notes
    """
    if not docstring:
        return {
            "description": "",
            "args": [],
            "returns": None,
            "raises": [],
            "examples": [],
            "notes": []
        }
    
    # Normalize line endings
    docstring = docstring.replace('\r\n', '\n').replace('\r', '\n')
    
    # Split into lines
    lines = docstring.strip().split('\n')
    
    result = {
        "description": "",
        "args": [],
        "returns": None,
        "raises": [],
        "examples": [],
        "notes": []
    }
    
    current_section = "description"
    current_content = []
    current_arg = None
    current_arg_desc = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for section headers
        if re.match(r'^Args?:', line, re.IGNORECASE):
            # Save previous description
            if current_content:
                result["description"] = '\n'.join(current_content).strip()
            current_content = []
            current_section = "args"
            i += 1
            continue
            
        elif re.match(r'^Returns?:', line, re.IGNORECASE):
            # Save previous arg if any
            if current_arg and current_arg_desc:
                result["args"].append((current_arg[0], current_arg[1], ' '.join(current_arg_desc).strip()))
            current_arg = None
            current_arg_desc = []
            current_section = "returns"
            i += 1
            continue
            
        elif re.match(r'^Raises?:', line, re.IGNORECASE):
            current_section = "raises"
            i += 1
            continue
            
        elif re.match(r'^Examples?:', line, re.IGNORECASE):
            current_section = "examples"
            i += 1
            continue
            
        elif re.match(r'^Notes?:', line, re.IGNORECASE):
            current_section = "notes"
            i += 1
            continue
        
        # Process line based on current section
        if current_section == "description":
            current_content.append(line)
            
        elif current_section == "args":
            # Look for parameter definitions: "param_name: type - description"
            # or "param_name (type): description"
            arg_match = re.match(r'^(\w+)(?:\s*[:\-]\s*([^:]+))?(?:\s*[:\-]\s*(.+))?$', line)
            if arg_match:
                # Save previous arg
                if current_arg and current_arg_desc:
                    result["args"].append((current_arg[0], current_arg[1], ' '.join(current_arg_desc).strip()))
                
                param_name = arg_match.group(1)
                param_type = arg_match.group(2) or ""
                param_desc = arg_match.group(3) or ""
                
                current_arg = (param_name, param_type.strip())
                current_arg_desc = [param_desc] if param_desc else []
            elif line and current_arg:
                # Continuation of current arg description
                current_arg_desc.append(line)
            elif not line:
                # Empty line - save current arg
                if current_arg and current_arg_desc:
                    result["args"].append((current_arg[0], current_arg[1], ' '.join(current_arg_desc).strip()))
                current_arg = None
                current_arg_desc = []
                
        elif current_section == "returns":
            if line:
                if result["returns"]:
                    result["returns"] += " " + line
                else:
                    result["returns"] = line
                    
        elif current_section == "raises":
            # Look for exception definitions: "ExceptionType: description"
            raise_match = re.match(r'^(\w+(?:Error|Exception)?)(?:\s*:\s*(.+))?$', line)
            if raise_match:
                exc_type = raise_match.group(1)
                exc_desc = raise_match.group(2) or ""
                result["raises"].append((exc_type, exc_desc))
                
        elif current_section == "examples":
            if line:
                result["examples"].append(line)
                
        elif current_section == "notes":
            if line:
                result["notes"].append(line)
        
        i += 1
    
    # Save final content
    if current_section == "description" and current_content:
        result["description"] = '\n'.join(current_content).strip()
    elif current_section == "args" and current_arg and current_arg_desc:
        result["args"].append((current_arg[0], current_arg[1], ' '.join(current_arg_desc).strip()))
    
    return result


def format_docstring_html(docstring: str) -> str:
    """Format a docstring as HTML for display in the UI.
    
    Args:
        docstring: The raw docstring text
        
    Returns:
        HTML formatted string
    """
    parsed = parse_docstring(docstring)
    
    html_parts = []
    
    # Description
    if parsed["description"]:
        html_parts.append(f'<div class="docstring-description">{_format_text(parsed["description"])}</div>')
    
    # Args
    if parsed["args"]:
        html_parts.append('<div class="docstring-section">')
        html_parts.append('<h5 class="docstring-section-title">Parameters</h5>')
        html_parts.append('<dl class="docstring-args">')
        for name, type_hint, desc in parsed["args"]:
            html_parts.append(f'<dt><code>{name}</code>')
            if type_hint:
                html_parts.append(f' <span class="type-hint">({type_hint})</span>')
            html_parts.append('</dt>')
            if desc:
                html_parts.append(f'<dd>{_format_text(desc)}</dd>')
        html_parts.append('</dl>')
        html_parts.append('</div>')
    
    # Returns
    if parsed["returns"]:
        html_parts.append('<div class="docstring-section">')
        html_parts.append('<h5 class="docstring-section-title">Returns</h5>')
        html_parts.append(f'<div class="docstring-returns">{_format_text(parsed["returns"])}</div>')
        html_parts.append('</div>')
    
    # Raises
    if parsed["raises"]:
        html_parts.append('<div class="docstring-section">')
        html_parts.append('<h5 class="docstring-section-title">Raises</h5>')
        html_parts.append('<dl class="docstring-raises">')
        for exc_type, desc in parsed["raises"]:
            html_parts.append(f'<dt><code>{exc_type}</code></dt>')
            if desc:
                html_parts.append(f'<dd>{_format_text(desc)}</dd>')
        html_parts.append('</dl>')
        html_parts.append('</div>')
    
    # Examples
    if parsed["examples"]:
        html_parts.append('<div class="docstring-section">')
        html_parts.append('<h5 class="docstring-section-title">Examples</h5>')
        html_parts.append('<pre class="docstring-examples"><code>')
        html_parts.append('\n'.join(parsed["examples"]))
        html_parts.append('</code></pre>')
        html_parts.append('</div>')
    
    # Notes
    if parsed["notes"]:
        html_parts.append('<div class="docstring-section">')
        html_parts.append('<h5 class="docstring-section-title">Notes</h5>')
        html_parts.append(f'<div class="docstring-notes">{_format_text(" ".join(parsed["notes"]))}</div>')
        html_parts.append('</div>')
    
    return '\n'.join(html_parts)


def format_docstring_markdown(docstring: str) -> str:
    """Format a docstring as Markdown for display.
    
    Args:
        docstring: The raw docstring text
        
    Returns:
        Markdown formatted string
    """
    parsed = parse_docstring(docstring)
    
    md_parts = []
    
    # Description
    if parsed["description"]:
        md_parts.append(parsed["description"])
        md_parts.append("")
    
    # Args
    if parsed["args"]:
        md_parts.append("**Parameters:**")
        md_parts.append("")
        for name, type_hint, desc in parsed["args"]:
            md_parts.append(f"- `{name}`")
            if type_hint:
                md_parts[-1] += f" ({type_hint})"
            if desc:
                md_parts[-1] += f": {desc}"
        md_parts.append("")
    
    # Returns
    if parsed["returns"]:
        md_parts.append("**Returns:**")
        md_parts.append("")
        md_parts.append(parsed["returns"])
        md_parts.append("")
    
    # Raises
    if parsed["raises"]:
        md_parts.append("**Raises:**")
        md_parts.append("")
        for exc_type, desc in parsed["raises"]:
            md_parts.append(f"- `{exc_type}`")
            if desc:
                md_parts[-1] += f": {desc}"
        md_parts.append("")
    
    # Examples
    if parsed["examples"]:
        md_parts.append("**Examples:**")
        md_parts.append("")
        md_parts.append("```")
        md_parts.extend(parsed["examples"])
        md_parts.append("```")
        md_parts.append("")
    
    # Notes
    if parsed["notes"]:
        md_parts.append("**Notes:**")
        md_parts.append("")
        md_parts.append(" ".join(parsed["notes"]))
        md_parts.append("")
    
    return '\n'.join(md_parts)


def _format_text(text: str) -> str:
    """Format plain text with basic markdown-like formatting.
    
    Args:
        text: Plain text to format
        
    Returns:
        HTML formatted text
    """
    # Escape HTML
    import html
    text = html.escape(text)
    
    # Convert code blocks
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Convert line breaks
    text = text.replace('\n', '<br>')
    
    return text
