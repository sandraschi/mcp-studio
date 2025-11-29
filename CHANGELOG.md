# Changelog

## [0.2.1] - 2025-11-29 - Detail Modal Redesign

### Improved
- **Redesigned detail modal** with comprehensive repo analysis:
  - 6-stat header row: FastMCP version, Portmanteaus, Operations, Individual tools, CI/CD, Zoo Class
  - Structure badge row: src/, tests/, scripts/, tools/, portmanteau presence indicators
  - Side-by-side Issues (🚨) and Recommendations (💡) panels
  - Collapsible README preview with full content
  - Organized tool list: Portmanteau section (📦) with operations, Individual section (🔹)
  - Each tool shows name, file path, and expandable docstring
- Better visual hierarchy with color-coded status badges
- Improved contrast and readability

## [0.2.0] - 2025-11-29 - MCP Zoo Runt Analyzer

### Added
- **MCP Zoo Runt Analyzer** (`runt_api.py`) - Standalone dashboard for analyzing MCP server quality
- Real-time progress reporting with SSE streaming
- Log collection and display in dashboard
- Detailed repo analysis modal with:
  - README preview
  - Tool list with docstrings (collapsible)
  - Portmanteau vs Individual tool classification
  - Operations count within portmanteaus
- Zoo classification system: 🐘 Jumbo, 🦁 Large, 🦊 Medium, 🐰 Small, 🐿️ Chipmunk
- Status classification: ✅ SOTA, ⚠️ Improvable, 🐛 Runt, 💀 Critical

### Analysis Criteria
- FastMCP version check (< 2.10 = runt, 2.10-2.11 = improvable)
- Project structure validation: `src/`, `tests/`, `scripts/`, `tools/`
- CI/CD workflow presence
- Tool registration pattern detection (decorator vs non-conforming)
- Portmanteau pattern adoption for large tool counts

### Technical
- Fast directory scanning with skip-dirs optimization
- Depth-limited file globbing for performance
- Async API with progress updates
- Tailwind CSS dashboard UI

## [0.1.0] - 2025-08-08 - Initial Release

### Added
- Initial project setup with FastAPI and FastMCP 2.11 integration
- Basic server management UI
- Stdio transport implementation
- CI/CD pipeline with GitHub Actions
- Automated release process
- Development tooling and pre-commit hooks
