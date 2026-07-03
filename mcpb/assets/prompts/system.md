# mcp-studio — MCP Server Capabilities

**Instructions for LLM:** This file must contain 3,000+ words describing the server's complete capabilities.
Include: all tools with parameters, all prompts, all resources, configuration options, environment variables,
data sources, and integration points. Every tool must have its purpose, parameters, and return format documented.

## Server Overview

[Write 2-3 paragraphs describing what this MCP server does, its domain, and key features.]

## Tools

- **get_current_working_set**: Get currently active working set. - **get_working_set**: Get specific working set details. - **switch_working_set**: Switch to specified working set with backup and rollback protection. - **create_backup**: Create backup of current config. - **restore_backup**: Restore config from backup. - **health_check**: Health check endpoint. - **discover_mcp_servers**: discover_mcp_servers - **discover_clients**: discover_clients - **get_server_info**: get_server_info - **list_server_tools**: list_server_tools - **get_client_config**: get_client_config - **set_client_config**: set_client_config - **execute_remote_tool**: execute_remote_tool - **test_server_connection**: test_server_connection - **help**: help - **set_discovery_path**: set_discovery_path - **status**: status - **analyze_repo_sota_status**: analyze_repo_sota_status - **create_mcp_server**: create_mcp_server - **update_mcp_server**: update_mcp_server - **delete_mcp_server**: delete_mcp_server - **scan_repos_for_sota_compliance**: scan_repos_for_sota_compliance - **read_own_items**: read_own_items - **download_file**: download_file - **list_groups**: List all tool groups (predefined + custom). - **get_active_groups**: Get currently active groups and servers. - **activate_group**: Activate a single group. - **deactivate_group**: Deactivate a single group. - **toggle_group**: Toggle a group's active status. - **activate_groups**: Activate multiple groups at once. - **deactivate_all**: Deactivate all groups. - **create_custom_group**: Create a custom tool group. - **delete_custom_group**: Delete a custom group. - **suggest_groups**: suggest_groups - **get_context_budget**: Get context budget usage for active groups. - **get_repos**: get_repos - **start_repo_scan**: start_repo_scan - **run_repo_scan**: run_repo_scan - **get_repos_summary**: get_repos_summary - **get_repo_details**: get_repo_details - **get_scan_progress**: Get real-time progress of the current scan. - **test_endpoint**: Simple test endpoint to verify routing works. - **get_thresholds**: Get current SOTA thresholds and criteria for repo scanning. - **update_settings_endpoint**: Update application settings.      Only updates the provided fields. - **reset_settings**: Reset all settings to defaults.      This will reload the application configuration from environm... - **test_single_server**: test_single_server - **test_all_servers**: test_all_servers - **quick_test**: quick_test - **my_tool**: my_tool

## Configuration

[Document all environment variables, their defaults, and purposes.]

## Data Sources

[Document any databases, APIs, or files the server reads.]
