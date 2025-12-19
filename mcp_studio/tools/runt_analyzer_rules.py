"""Declarative rule system for SOTA compliance evaluation.

This module provides a clean, maintainable rule-based system for evaluating
MCP repository SOTA compliance. Rules are defined declaratively and can be
easily modified or extended without touching evaluation logic.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class RuleSeverity(Enum):
    """Severity levels for rule violations."""
    CRITICAL = "critical"  # Makes repo a runt
    WARNING = "warning"    # Adds to recommendations
    INFO = "info"          # Minor suggestion


class RuleCategory(Enum):
    """Categories for organizing rules."""
    VERSION = "version"
    TOOLS = "tools"
    STRUCTURE = "structure"
    QUALITY = "quality"
    TESTING = "testing"
    CI_CD = "ci_cd"
    DOCUMENTATION = "documentation"


@dataclass
class Rule:
    """A single SOTA compliance rule."""
    id: str
    name: str
    category: RuleCategory
    severity: RuleSeverity
    description: str
    recommendation: str
    
    # Rule evaluation
    check: Callable[[Dict[str, Any]], bool]
    
    # Scoring
    score_deduction: int = 0  # Points to deduct from SOTA score
    score_condition: Optional[Callable[[Dict[str, Any]], int]] = None  # Dynamic deduction
    
    # Condition for when rule applies
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None  # Only check if condition is True
    
    # Message formatting
    message_template: Optional[str] = None  # Custom message format
    
    def evaluate(self, info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate rule against repo info.
        
        Returns:
            Dict with violation details if rule fails, None if passes
        """
        # Check if rule applies
        if self.condition and not self.condition(info):
            return None
        
        # Check if rule is violated
        if not self.check(info):
            return None
        
        # Rule violated - return violation details
        message = self._format_message(info)
        score_deduction = self._calculate_deduction(info)
        
        return {
            "rule_id": self.id,
            "rule_name": self.name,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": message,
            "recommendation": self.recommendation,
            "score_deduction": score_deduction,
        }
    
    def _format_message(self, info: Dict[str, Any]) -> str:
        """Format violation message."""
        if self.message_template:
            try:
                return self.message_template.format(**info)
            except KeyError:
                pass
        return self.description
    
    def _calculate_deduction(self, info: Dict[str, Any]) -> int:
        """Calculate score deduction for this violation."""
        if self.score_condition:
            return self.score_condition(info)
        return self.score_deduction


# ============================================================================
# RULE DEFINITIONS
# ============================================================================

def _version_check(info: Dict[str, Any]) -> bool:
    """Check if FastMCP version is too old."""
    version = info.get("fastmcp_version")
    if not version:
        return True  # No version = violation
    
    try:
        version_parts = [int(x) for x in version.split('.')[:2]]
        threshold_parts = [int(x) for x in "2.12.0".split('.')[:2]]
        return version_parts < threshold_parts
    except Exception:
        return True  # Invalid version = violation


def _portmanteau_needed(info: Dict[str, Any]) -> bool:
    """Check if portmanteau pattern is needed but missing."""
    tool_count = info.get("tool_count", 0)
    has_portmanteau = info.get("has_portmanteau", False)
    return tool_count > 15 and not has_portmanteau


def _tool_count_condition(info: Dict[str, Any]) -> bool:
    """Rule only applies if repo has tools."""
    return info.get("tool_count", 0) > 0


def _large_repo_condition(info: Dict[str, Any]) -> bool:
    """Rule only applies to larger repos."""
    return info.get("tool_count", 0) >= 10


def _many_prints_condition(info: Dict[str, Any]) -> bool:
    """Check if there are many print statements."""
    return info.get("print_statement_count", 0) > 5


def _dynamic_print_deduction(info: Dict[str, Any]) -> int:
    """Calculate deduction based on print count."""
    count = info.get("print_statement_count", 0)
    if count > 5:
        return 10
    elif count > 0:
        return 5
    return 0


def _dynamic_lazy_error_deduction(info: Dict[str, Any]) -> int:
    """Calculate deduction based on lazy error count."""
    count = info.get("lazy_error_msg_count", 0)
    if count >= 5:
        return 10
    elif count > 0:
        return 5
    return 0


# Rule registry
SOTA_RULES: List[Rule] = [
    # Version Rules
    Rule(
        id="fastmcp_version",
        name="FastMCP Version",
        category=RuleCategory.VERSION,
        severity=RuleSeverity.CRITICAL,
        description="FastMCP version is too old",
        recommendation="Upgrade to FastMCP 2.13.1",
        check=_version_check,
        score_deduction=20,
        message_template="FastMCP {fastmcp_version} < 2.12.0",
    ),
    
    # Tool Rules
    Rule(
        id="portmanteau_missing",
        name="Portmanteau Pattern",
        category=RuleCategory.TOOLS,
        severity=RuleSeverity.CRITICAL,
        description="Many tools without portmanteau pattern",
        recommendation="Refactor to portmanteau tools",
        check=_portmanteau_needed,
        score_deduction=25,
        message_template="{tool_count} tools without portmanteau (threshold: 15)",
    ),
    
    Rule(
        id="help_tool_missing",
        name="Help Tool",
        category=RuleCategory.TOOLS,
        severity=RuleSeverity.CRITICAL,
        description="No help tool",
        recommendation="Add help() tool for discoverability",
        check=lambda info: not info.get("has_help_tool", False),
        condition=_tool_count_condition,
        score_deduction=10,
    ),
    
    Rule(
        id="status_tool_missing",
        name="Status Tool",
        category=RuleCategory.TOOLS,
        severity=RuleSeverity.CRITICAL,
        description="No status tool",
        recommendation="Add status() tool for diagnostics",
        check=lambda info: not info.get("has_status_tool", False),
        condition=_tool_count_condition,
        score_deduction=10,
    ),
    
    # CI/CD Rules
    Rule(
        id="ci_missing",
        name="CI/CD Workflows",
        category=RuleCategory.CI_CD,
        severity=RuleSeverity.CRITICAL,
        description="No CI/CD workflows",
        recommendation="Add CI workflow with ruff + pytest",
        check=lambda info: not info.get("has_ci", False),
        condition=_large_repo_condition,
        score_deduction=20,
    ),
    
    Rule(
        id="ci_too_many",
        name="CI Workflow Count",
        category=RuleCategory.CI_CD,
        severity=RuleSeverity.WARNING,
        description="Too many CI workflows",
        recommendation="Consolidate to single CI workflow",
        check=lambda info: info.get("ci_workflows", 0) > 3,
        score_deduction=5,
        message_template="{ci_workflows} CI workflows (recommend: 1)",
    ),
    
    # Structure Rules
    Rule(
        id="dxt_missing",
        name="DXT Packaging",
        category=RuleCategory.STRUCTURE,
        severity=RuleSeverity.WARNING,
        description="No DXT packaging",
        recommendation="Add manifest.json for desktop extension support",
        check=lambda info: not info.get("has_dxt", False),
        score_deduction=10,
    ),
    
    Rule(
        id="tests_missing",
        name="Test Directory",
        category=RuleCategory.TESTING,
        severity=RuleSeverity.CRITICAL,
        description="No test directory",
        recommendation="Add tests/ directory with unit tests",
        check=lambda info: not info.get("has_tests", False),
        condition=_large_repo_condition,
        score_deduction=15,
    ),
    
    Rule(
        id="unit_tests_missing",
        name="Unit Tests",
        category=RuleCategory.TESTING,
        severity=RuleSeverity.WARNING,
        description="No unit tests",
        recommendation="Add tests/unit/ with test_*.py files",
        check=lambda info: not info.get("has_unit_tests", False),
        condition=lambda info: info.get("has_tests", False),
        score_deduction=5,
    ),
    
    Rule(
        id="integration_tests_missing",
        name="Integration Tests",
        category=RuleCategory.TESTING,
        severity=RuleSeverity.WARNING,
        description="No integration tests",
        recommendation="Add tests/integration/ for API/E2E tests",
        check=lambda info: not info.get("has_integration_tests", False),
        condition=lambda info: info.get("has_tests", False),
        score_deduction=5,
    ),
    
    Rule(
        id="test_count_low",
        name="Test Coverage",
        category=RuleCategory.TESTING,
        severity=RuleSeverity.WARNING,
        description="Low test file count",
        recommendation="Add more test coverage",
        check=lambda info: info.get("test_file_count", 0) < 3,
        condition=lambda info: info.get("has_tests", False),
        score_deduction=0,  # Info only
        message_template="Only {test_file_count} test files (recommend: 5+)",
    ),
    
    # Quality Rules
    Rule(
        id="ruff_missing",
        name="Ruff Linting",
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.CRITICAL,
        description="No ruff linting configured",
        recommendation="Add ruff to pyproject.toml and CI workflow",
        check=lambda info: not info.get("has_ruff", False),
        score_deduction=10,
    ),
    
    Rule(
        id="logging_missing",
        name="Proper Logging",
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.CRITICAL,
        description="No proper logging",
        recommendation="Add structlog or logging module for observability",
        check=lambda info: not info.get("has_proper_logging", False),
        score_deduction=10,
    ),
    
    Rule(
        id="print_statements",
        name="Print Statements",
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.WARNING,
        description="Print statements in code",
        recommendation="Replace print() with logger calls",
        check=lambda info: info.get("print_statement_count", 0) > 0,
        score_condition=_dynamic_print_deduction,
        message_template="{print_statement_count} print() calls in non-test code",
    ),
    
    Rule(
        id="print_statements_many",
        name="Excessive Print Statements",
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.CRITICAL,
        description="Too many print statements",
        recommendation="Replace print() with logger calls",
        check=_many_prints_condition,
        score_deduction=10,
        message_template="{print_statement_count} print() calls (too many)",
    ),
    
    Rule(
        id="bare_except",
        name="Bare Except Clauses",
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.CRITICAL,
        description="Bare except clauses",
        recommendation="Use specific exception types (ValueError, TypeError, etc.)",
        check=lambda info: info.get("bare_except_count", 0) >= 3,
        score_deduction=10,
        message_template="{bare_except_count} bare except clauses",
    ),
    
    Rule(
        id="lazy_errors",
        name="Non-Informative Errors",
        category=RuleCategory.QUALITY,
        severity=RuleSeverity.WARNING,
        description="Non-informative error messages",
        recommendation="Use descriptive error messages with context",
        check=lambda info: info.get("lazy_error_msg_count", 0) > 0,
        score_condition=_dynamic_lazy_error_deduction,
        message_template="{lazy_error_msg_count} non-informative error messages",
    ),
    
    # Documentation Rules
    Rule(
        id="docstrings_missing",
        name="Proper Docstrings",
        category=RuleCategory.DOCUMENTATION,
        severity=RuleSeverity.WARNING,
        description="Missing proper docstrings",
        recommendation="Add comprehensive docstrings with Args, Returns, Examples",
        check=lambda info: not info.get("has_proper_docstrings", False),
        condition=_tool_count_condition,
        score_deduction=10,
    ),
    
    Rule(
        id="pytest_config_missing",
        name="Pytest Configuration",
        category=RuleCategory.TESTING,
        severity=RuleSeverity.WARNING,
        description="No pytest configuration",
        recommendation="Add [tool.pytest.ini_options] to pyproject.toml",
        check=lambda info: not info.get("has_pytest_config", False),
        score_deduction=5,
    ),
    
    Rule(
        id="coverage_config_missing",
        name="Coverage Configuration",
        category=RuleCategory.TESTING,
        severity=RuleSeverity.WARNING,
        description="No coverage configuration",
        recommendation="Add [tool.coverage] to pyproject.toml",
        check=lambda info: not info.get("has_coverage_config", False),
        score_deduction=5,
    ),
]


def evaluate_rules(info: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate all rules against repo info.
    
    Returns:
        Dict with violations, score deduction, and runt status
    """
    violations: List[Dict[str, Any]] = []
    critical_violations: List[Dict[str, Any]] = []
    total_deduction = 0
    
    for rule in SOTA_RULES:
        violation = rule.evaluate(info)
        if violation:
            violations.append(violation)
            total_deduction += violation["score_deduction"]
            
            if rule.severity == RuleSeverity.CRITICAL:
                critical_violations.append(violation)
    
    # Determine runt status
    is_runt = len(critical_violations) > 0
    
    # Build runt reasons and recommendations
    runt_reasons = [v["message"] for v in violations]
    recommendations = [v["recommendation"] for v in violations]
    
    # Remove duplicates while preserving order
    seen_reasons = set()
    unique_reasons = []
    for reason in runt_reasons:
        if reason not in seen_reasons:
            seen_reasons.add(reason)
            unique_reasons.append(reason)
    
    seen_recs = set()
    unique_recommendations = []
    for rec in recommendations:
        if rec not in seen_recs:
            seen_recs.add(rec)
            unique_recommendations.append(rec)
    
    return {
        "violations": violations,
        "critical_violations": critical_violations,
        "is_runt": is_runt,
        "runt_reasons": unique_reasons,
        "recommendations": unique_recommendations,
        "score_deduction": total_deduction,
        "violation_count": len(violations),
        "critical_count": len(critical_violations),
    }


def calculate_sota_score(info: Dict[str, Any], base_score: int = 100) -> int:
    """Calculate SOTA compliance score.
    
    Args:
        info: Repository information
        base_score: Starting score (default: 100)
    
    Returns:
        Score from 0-100
    """
    result = evaluate_rules(info)
    score = base_score - result["score_deduction"]
    return max(0, min(100, score))


def get_rules_by_category(category: Optional[RuleCategory] = None) -> List[Rule]:
    """Get rules, optionally filtered by category."""
    if category:
        return [r for r in SOTA_RULES if r.category == category]
    return SOTA_RULES.copy()


def get_rule_by_id(rule_id: str) -> Optional[Rule]:
    """Get a specific rule by ID."""
    for rule in SOTA_RULES:
        if rule.id == rule_id:
            return rule
    return None
