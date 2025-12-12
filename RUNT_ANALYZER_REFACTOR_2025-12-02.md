# Runt Analyzer Refactoring - 2025-12-02

## Summary

Refactored the runt analyzer from hardcoded criteria and point system to an elegant, declarative rule-based architecture.

## Problem

**Before:** Hardcoded criteria scattered throughout code
- Point deductions hardcoded in `_calculate_sota_score()` (-20, -25, -10, -5)
- Thresholds hardcoded as constants (FASTMCP_RUNT_THRESHOLD, TOOL_PORTMANTEAU_THRESHOLD)
- Evaluation logic mixed with rule definitions (100+ lines of if/else)
- Difficult to modify or extend rules
- No clear separation of concerns

## Solution

**After:** Declarative rule-based system
- Rules defined as data structures (dataclasses)
- Rule evaluation separated from rule definitions
- Easy to add/modify rules without touching evaluation logic
- Configurable scoring with dynamic deductions
- Rule categories and severity levels
- Extensible and maintainable

## Architecture

### New Module: `runt_analyzer_rules.py`

**Core Components:**

1. **Rule Dataclass**
   ```python
   @dataclass
   class Rule:
       id: str
       name: str
       category: RuleCategory
       severity: RuleSeverity
       check: Callable[[Dict], bool]
       score_deduction: int
       condition: Optional[Callable]  # When rule applies
   ```

2. **Rule Categories**
   - VERSION
   - TOOLS
   - STRUCTURE
   - QUALITY
   - TESTING
   - CI_CD
   - DOCUMENTATION

3. **Severity Levels**
   - CRITICAL: Makes repo a runt
   - WARNING: Adds to recommendations
   - INFO: Minor suggestion

4. **Rule Registry**
   - All rules defined in `SOTA_RULES` list
   - Easy to add new rules
   - Rules are self-contained

### Example Rule Definition

**Before (hardcoded):**
```python
# Check help tool
if not info["has_help_tool"]:
    info["is_runt"] = True
    info["runt_reasons"].append("No help tool")
    info["recommendations"].append("Add help() tool for discoverability")
# ... scattered in 100+ lines
```

**After (declarative):**
```python
Rule(
    id="help_tool_missing",
    name="Help Tool",
    category=RuleCategory.TOOLS,
    severity=RuleSeverity.CRITICAL,
    description="No help tool",
    recommendation="Add help() tool for discoverability",
    check=lambda info: not info.get("has_help_tool", False),
    condition=_tool_count_condition,  # Only applies if repo has tools
    score_deduction=10,
)
```

## Benefits

### 1. **Maintainability**
- All rules in one place
- Easy to see all criteria at a glance
- Clear rule structure

### 2. **Extensibility**
- Add new rules by adding to `SOTA_RULES` list
- No need to modify evaluation logic
- Rules are self-documenting

### 3. **Flexibility**
- Dynamic score deductions via `score_condition`
- Conditional rule application via `condition`
- Custom message formatting via `message_template`

### 4. **Testability**
- Rules can be tested independently
- Evaluation logic is separate
- Easy to mock rules for testing

### 5. **Clarity**
- Rule intent is clear from definition
- Categories organize related rules
- Severity levels make impact obvious

## Rule Features

### Conditional Application
```python
Rule(
    id="ci_missing",
    condition=_large_repo_condition,  # Only check for repos with >=10 tools
    ...
)
```

### Dynamic Scoring
```python
Rule(
    id="print_statements",
    score_condition=_dynamic_print_deduction,  # -5 for few, -10 for many
    ...
)
```

### Custom Messages
```python
Rule(
    id="portmanteau_missing",
    message_template="{tool_count} tools without portmanteau (threshold: 15)",
    ...
)
```

## Migration

**Backward Compatibility:**
- Old constants kept for compatibility
- Same output format maintained
- No breaking changes to API

**Evaluation Flow:**
1. `_analyze_repo()` collects repo information
2. `_evaluate_runt_status()` calls `evaluate_rules()`
3. Rules are evaluated against repo info
4. Results formatted into existing structure

## Code Reduction

**Before:**
- `_evaluate_runt_status()`: ~110 lines of if/else
- `_calculate_sota_score()`: ~85 lines of deductions
- **Total:** ~195 lines of hardcoded logic

**After:**
- Rule definitions: ~200 lines (declarative, readable)
- Evaluation logic: ~30 lines (generic, reusable)
- **Total:** ~230 lines but much more maintainable

**Net Result:** Slightly more code, but:
- Much easier to understand
- Much easier to modify
- Much easier to extend
- Better separation of concerns

## Example: Adding a New Rule

**Before:**
1. Add check in `_evaluate_runt_status()`
2. Add deduction in `_calculate_sota_score()`
3. Update multiple places
4. Risk breaking existing logic

**After:**
```python
Rule(
    id="new_feature_check",
    name="New Feature",
    category=RuleCategory.QUALITY,
    severity=RuleSeverity.WARNING,
    description="Missing new feature",
    recommendation="Add new feature",
    check=lambda info: not info.get("has_new_feature", False),
    score_deduction=5,
)
# Just add to SOTA_RULES list - done!
```

## Future Enhancements

1. **Rule Configuration File**
   - Load rules from YAML/JSON
   - Allow users to customize rules
   - Override default thresholds

2. **Rule Testing**
   - Unit tests for each rule
   - Test rule combinations
   - Validate rule logic

3. **Rule Documentation**
   - Auto-generate rule documentation
   - Explain why each rule exists
   - Provide examples

4. **Rule Analytics**
   - Track which rules fail most often
   - Identify common patterns
   - Suggest rule improvements

## Files Modified

1. **NEW:** `src/mcp_studio/tools/runt_analyzer_rules.py`
   - Rule definitions
   - Rule evaluation engine
   - Rule utilities

2. **UPDATED:** `src/mcp_studio/tools/runt_analyzer.py`
   - Imports rule system
   - Uses `evaluate_rules()` instead of hardcoded logic
   - Uses `calculate_sota_score()` from rules module

## Testing

The refactored system maintains the same behavior:
- Same violations detected
- Same scores calculated
- Same runt classifications
- Same recommendations generated

**Verification:**
- Run analyzer on test repos
- Compare results before/after
- Ensure no regressions

## Conclusion

The refactored rule-based system is:
- ✅ More elegant and maintainable
- ✅ Easier to extend and modify
- ✅ Better organized and documented
- ✅ More testable and debuggable
- ✅ Backward compatible

The hardcoded criteria have been replaced with a clean, declarative system that makes the analyzer more powerful and easier to work with.
