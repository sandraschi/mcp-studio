"""Markdown formatter for repository scan results.

Converts scan results to human-readable markdown format.
"""

from typing import Any, Dict, List
from datetime import datetime


def format_scan_result_markdown(result: Dict[str, Any]) -> str:
    """Format scan result as markdown.
    
    Args:
        result: Scan result dictionary
    
    Returns:
        Formatted markdown string
    """
    if not result.get("success"):
        return f"# Scan Failed\n\n**Error:** {result.get('error', 'Unknown error')}\n"
    
    md = []
    md.append("# MCP Repository Scan Results\n")
    
    # Summary
    summary = result.get("summary", {})
    md.append("## Summary\n")
    md.append(f"- **Total MCP Repos:** {summary.get('total_mcp_repos', 0)}")
    md.append(f"- **Runts:** {summary.get('runts', 0)}")
    md.append(f"- **SOTA:** {summary.get('sota', 0)}")
    md.append(f"- **Scan Path:** `{result.get('scan_path', 'N/A')}`")
    
    timestamp = result.get("timestamp")
    if timestamp:
        dt = datetime.fromtimestamp(timestamp)
        md.append(f"- **Scan Time:** {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    md.append("")
    
    # Runts
    runts = result.get("runts", [])
    if runts:
        md.append("## 🐛 Runts (Need Upgrades)\n")
        for runt in runts:
            md.append(f"### {runt.get('status_emoji', '🐛')} {runt.get('name', 'Unknown')}")
            md.append(f"**Status:** {runt.get('status_label', 'Unknown')}")
            md.append(f"**SOTA Score:** {runt.get('sota_score', 0)}/100")
            md.append(f"**FastMCP Version:** {runt.get('fastmcp_version', 'Unknown')}")
            md.append(f"**Tool Count:** {runt.get('tool_count', 0)}")
            md.append("")
            
            reasons = runt.get("runt_reasons", [])
            if reasons:
                md.append("**Issues:**")
                for reason in reasons:
                    md.append(f"- {reason}")
                md.append("")
            
            recommendations = runt.get("recommendations", [])
            if recommendations:
                md.append("**Recommendations:**")
                for rec in recommendations:
                    md.append(f"- {rec}")
                md.append("")
            
            md.append("---\n")
    
    # SOTA Repos
    sota_repos = result.get("sota_repos", [])
    if sota_repos:
        md.append("## ✅ SOTA Repositories\n")
        for repo in sota_repos:
            md.append(f"### {repo.get('status_emoji', '✅')} {repo.get('name', 'Unknown')}")
            md.append(f"**Status:** {repo.get('status_label', 'SOTA')}")
            md.append(f"**SOTA Score:** {repo.get('sota_score', 100)}/100")
            md.append(f"**FastMCP Version:** {repo.get('fastmcp_version', 'Unknown')}")
            md.append(f"**Tool Count:** {repo.get('tool_count', 0)}")
            md.append(f"**Zoo Class:** {repo.get('zoo_class', 'unknown')} {repo.get('zoo_animal', '')}")
            md.append("")
            md.append("---\n")
    
    return "\n".join(md)


def format_repo_status_markdown(result: Dict[str, Any]) -> str:
    """Format single repo status as markdown.
    
    Args:
        result: Repo status dictionary
    
    Returns:
        Formatted markdown string
    """
    if not result.get("success"):
        return f"# Repository Status Failed\n\n**Error:** {result.get('error', 'Unknown error')}\n"
    
    md = []
    md.append(f"# {result.get('name', 'Unknown Repository')}\n")
    
    # Status Overview
    md.append("## Status Overview\n")
    md.append(f"**Status:** {result.get('status_emoji', '✅')} {result.get('status_label', 'Unknown')}")
    md.append(f"**SOTA Score:** {result.get('sota_score', 0)}/100")
    md.append(f"**Upgrade Priority:** {result.get('upgrade_priority', 'N/A')}")
    md.append(f"**Path:** `{result.get('path', 'N/A')}`")
    md.append("")
    
    # Basic Info
    md.append("## Basic Information\n")
    md.append(f"- **FastMCP Version:** {result.get('fastmcp_version', 'Unknown')}")
    md.append(f"- **Tool Count:** {result.get('tool_count', 0)}")
    md.append(f"- **Has Portmanteau:** {'Yes' if result.get('has_portmanteau') else 'No'}")
    md.append(f"- **Zoo Class:** {result.get('zoo_class', 'unknown')} {result.get('zoo_animal', '')}")
    md.append("")
    
    # Issues
    reasons = result.get("runt_reasons", [])
    if reasons:
        md.append("## Issues\n")
        for reason in reasons:
            md.append(f"- ❌ {reason}")
        md.append("")
    
    # Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        md.append("## Recommendations\n")
        for rec in recommendations:
            md.append(f"- 💡 {rec}")
        md.append("")
    
    # Detailed Information
    details = result.get("details")
    if details:
        md.append("## Detailed Information\n")
        
        # Metadata
        metadata = details.get("metadata", {})
        if metadata:
            md.append("### Metadata\n")
            if metadata.get("description"):
                md.append(f"**Description:** {metadata['description']}")
            if metadata.get("author"):
                md.append(f"**Author:** {metadata['author']}")
            if metadata.get("version"):
                md.append(f"**Version:** {metadata['version']}")
            if metadata.get("license_type"):
                md.append(f"**License:** {metadata['license_type']}")
            md.append("")
        
        # Dependencies
        deps = details.get("dependencies", {})
        if deps:
            md.append("### Dependencies\n")
            md.append(f"- **FastMCP:** {deps.get('fastmcp_version', 'Unknown')}")
            md.append(f"- **Total Dependencies:** {deps.get('total_dependencies', 0)}")
            python_deps = deps.get("python_dependencies", [])
            if python_deps:
                md.append(f"- **Python Packages:** {', '.join(python_deps[:10])}")
                if len(python_deps) > 10:
                    md.append(f"  *... and {len(python_deps) - 10} more*")
            md.append("")
        
        # Tools
        tools = details.get("tools", {})
        if tools:
            md.append("### Tools\n")
            md.append(f"- **Total Tools:** {tools.get('total_count', 0)}")
            md.append(f"- **Has Help Tool:** {'Yes' if tools.get('has_help_tool') else 'No'}")
            md.append(f"- **Has Status Tool:** {'Yes' if tools.get('has_status_tool') else 'No'}")
            
            tool_list = tools.get("tools", [])
            if tool_list:
                md.append("\n**Tool List:**")
                for tool in tool_list[:20]:  # Limit to first 20
                    md.append(f"- `{tool.get('name', 'unknown')}` ({tool.get('type', 'unknown')})")
                if len(tool_list) > 20:
                    md.append(f"  *... and {len(tool_list) - 20} more*")
            md.append("")
        
        # Structure
        structure = details.get("structure", {})
        if structure:
            md.append("### Structure\n")
            md.append(f"- **Layout:** {'src/' if structure.get('has_src_layout') else 'flat'}")
            md.append(f"- **Main Package:** {structure.get('main_package', 'N/A')}")
            file_counts = structure.get("file_counts", {})
            if file_counts:
                md.append(f"- **Python Files:** {file_counts.get('python', 0)}")
                md.append(f"- **Markdown Files:** {file_counts.get('markdown', 0)}")
            md.append("")
        
        # Testing
        testing = details.get("testing", {})
        if testing:
            md.append("### Testing\n")
            md.append(f"- **Has Tests:** {'Yes' if testing.get('has_tests') else 'No'}")
            if testing.get('has_tests'):
                md.append(f"- **Test Files:** {testing.get('test_file_count', 0)}")
                md.append(f"- **Framework:** {testing.get('test_framework', 'Unknown')}")
                md.append(f"- **Unit Tests:** {'Yes' if testing.get('has_unit_tests') else 'No'}")
                md.append(f"- **Integration Tests:** {'Yes' if testing.get('has_integration_tests') else 'No'}")
            md.append("")
        
        # CI/CD
        ci_cd = details.get("ci_cd", {})
        if ci_cd:
            md.append("### CI/CD\n")
            md.append(f"- **Has CI:** {'Yes' if ci_cd.get('has_ci') else 'No'}")
            if ci_cd.get('has_ci'):
                md.append(f"- **Provider:** {ci_cd.get('ci_provider', 'Unknown')}")
                md.append(f"- **Workflows:** {ci_cd.get('workflow_count', 0)}")
            md.append("")
    
    # Timestamp
    timestamp = result.get("timestamp")
    if timestamp:
        dt = datetime.fromtimestamp(timestamp)
        md.append(f"---\n*Generated: {dt.strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(md)
