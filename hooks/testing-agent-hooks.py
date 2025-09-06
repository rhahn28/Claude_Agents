#!/usr/bin/env python3
"""
Testing-specific hooks for test-automation-expert, qa-specialist
Validates test coverage, quality, and testing best practices
"""

import json
import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def analyze_test_coverage(content: str, file_path: str) -> tuple[str, list]:
    """Analyze test coverage and completeness"""
    
    coverage_issues = []
    
    # Check if this is a test file
    is_test_file = any(test_indicator in file_path.lower() for test_indicator in ["test", "spec", "_test.py", ".test.js", ".spec.js"])
    
    if is_test_file:
        # Test structure analysis
        test_functions = re.findall(r'def\s+(test_\w+)', content)
        test_methods = re.findall(r'test\(\s*[\'"]([^\'"]*)[\'"]', content)
        it_blocks = re.findall(r'it\(\s*[\'"]([^\'"]*)[\'"]', content)
        describe_blocks = re.findall(r'describe\(\s*[\'"]([^\'"]*)[\'"]', content)
        
        total_tests = len(test_functions) + len(test_methods) + len(it_blocks)
        
        # Check test naming conventions
        for test_name in test_functions:
            if not re.match(r'test_[a-z][a-z0-9_]*', test_name):
                coverage_issues.append(f"📝 NAMING: Test '{test_name}' doesn't follow naming convention")
        
        # Check for essential test patterns
        essential_patterns = [
            (r'assert|expect', "Assertions found"),
            (r'mock|Mock|patch', "Mocking found"),
            (r'setUp|tearDown|beforeEach|afterEach', "Setup/teardown found"),
        ]
        
        missing_patterns = []
        for pattern, description in essential_patterns:
            if not re.search(pattern, content):
                missing_patterns.append(description.replace(" found", ""))
        
        if missing_patterns:
            coverage_issues.append(f"🔍 MISSING: {', '.join(missing_patterns)}")
        
        # Check test isolation
        if re.search(r'global|nonlocal', content) and total_tests > 1:
            coverage_issues.append("🔒 ISOLATION: Tests may not be isolated due to global state")
        
        # Check for test data patterns
        if not re.search(r'fixture|factory|Builder', content) and total_tests > 3:
            coverage_issues.append("🏭 DATA: Consider using test fixtures or factories for test data")
        
    else:
        # Production code - check for testability
        function_count = len(re.findall(r'def\s+\w+\s*\(', content))
        class_count = len(re.findall(r'class\s+\w+', content))
        
        if function_count > 5 or class_count > 2:
            # Look for corresponding test files
            potential_test_files = [
                file_path.replace('.py', '_test.py'),
                file_path.replace('.py', '.test.py'),
                file_path.replace('.js', '.test.js'),
                file_path.replace('.js', '.spec.js'),
                file_path.replace('src/', 'test/').replace('.py', '_test.py'),
            ]
            
            coverage_issues.append(f"🧪 TESTABILITY: Large file ({function_count} functions, {class_count} classes) - ensure adequate test coverage")
    
    # Risk assessment
    if len(coverage_issues) >= 3:
        return "MEDIUM", coverage_issues
    elif coverage_issues:
        return "LOW", coverage_issues
    
    return "NONE", []

def check_test_quality_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for test quality and anti-patterns"""
    
    quality_issues = []
    
    # Test anti-patterns
    anti_patterns = [
        (r'time\.sleep\(\d+\)', "ANTI-PATTERN: Hard-coded sleep in tests - use proper synchronization"),
        (r'assert\s+True\s*==\s*True|assert\s+1\s*==\s*1', "ANTI-PATTERN: Meaningless assertions"),
        (r'except.*:.*pass', "ANTI-PATTERN: Silently ignoring exceptions in tests"),
        (r'test.*\n.*test.*\n.*test', "ANTI-PATTERN: Multiple test methods without clear separation"),
        (r'random\.|Math\.random', "ANTI-PATTERN: Non-deterministic random values in tests"),
    ]
    
    # Test smells
    test_smells = [
        (r'assert.*and.*assert', "SMELL: Multiple assertions in single test - consider splitting"),
        (r'for.*in.*:.*assert', "SMELL: Assertions in loops - may mask failures"),
        (r'if.*assert.*else.*assert', "SMELL: Conditional assertions - tests should be deterministic"),
        (r'len\(.*\)\s*>\s*\d+.*assert', "SMELL: Testing collection size instead of specific content"),
    ]
    
    # Performance issues in tests
    performance_patterns = [
        (r'requests\.(get|post)', "PERFORMANCE: HTTP requests in tests - consider mocking"),
        (r'open\(.*[\'"]w[\'"]', "PERFORMANCE: File I/O in tests - consider in-memory alternatives"),
        (r'subprocess\.|os\.system', "PERFORMANCE: System calls in tests - consider mocking"),
        (r'Thread\(|Process\(', "PERFORMANCE: Threading/multiprocessing in tests - may cause flakiness"),
    ]
    
    for pattern, description in anti_patterns:
        if re.search(pattern, content):
            quality_issues.append(f"🚨 {description}")
    
    for pattern, description in test_smells:
        if re.search(pattern, content):
            quality_issues.append(f"👃 {description}")
    
    for pattern, description in performance_patterns:
        if re.search(pattern, content):
            quality_issues.append(f"⚡ {description}")
    
    # Count different issue types
    anti_pattern_count = len([issue for issue in quality_issues if "ANTI-PATTERN" in issue])
    smell_count = len([issue for issue in quality_issues if "SMELL" in issue])
    
    if anti_pattern_count >= 1:
        return "HIGH", quality_issues
    elif smell_count >= 2 or len(quality_issues) >= 3:
        return "MEDIUM", quality_issues
    elif quality_issues:
        return "LOW", quality_issues
    
    return "NONE", []

def validate_test_documentation(content: str, file_path: str) -> list:
    """Check for test documentation and clarity"""
    
    doc_issues = []
    
    # Check for test documentation
    if "test" in file_path.lower():
        test_functions = re.findall(r'def\s+(test_\w+)', content)
        
        for test_func in test_functions:
            # Look for docstring after function definition
            func_pattern = rf'def\s+{re.escape(test_func)}\s*\([^)]*\):\s*"""([^"]*)"""'
            if not re.search(func_pattern, content, re.DOTALL):
                doc_issues.append(f"📖 DOC: Test '{test_func}' missing docstring")
        
        # Check for test plan or readme
        if len(test_functions) > 10 and "README" not in content and "Test Plan" not in content:
            doc_issues.append("📋 DOC: Large test suite should have documentation or test plan")
    
    return doc_issues

def check_test_environment_setup(content: str, file_path: str) -> list:
    """Check test environment and dependencies"""
    
    env_issues = []
    
    # Check for proper test setup
    setup_patterns = [
        (r'@pytest\.fixture', "Pytest fixtures detected"),
        (r'setUp|tearDown', "xUnit setup detected"),
        (r'beforeEach|afterEach', "JavaScript test setup detected"),
        (r'@mock\.patch', "Python mocking detected"),
    ]
    
    has_setup = any(re.search(pattern, content) for pattern, _ in setup_patterns)
    
    # Check for resource cleanup
    cleanup_patterns = [
        (r'close\(\)|cleanup\(\)', "Resource cleanup detected"),
        (r'finally:|tearDown|afterEach', "Cleanup blocks detected"),
    ]
    
    has_cleanup = any(re.search(pattern, content) for pattern, _ in cleanup_patterns)
    
    # Check for external dependencies
    if re.search(r'requests\.|urllib\.|httplib', content):
        if not re.search(r'mock|Mock|patch|responses', content):
            env_issues.append("🌐 ENV: External HTTP calls without mocking - tests may be brittle")
    
    # Check for database operations
    if re.search(r'connection|cursor|execute\(', content):
        if not re.search(r'test.*db|memory|sqlite.*:memory:', content):
            env_issues.append("🗄️ ENV: Database operations without test database - may affect production data")
    
    # Check for file operations
    if re.search(r'open\(.*[\'"]w[\'"]|write\(', content):
        if not re.search(r'tempfile|tmp|test.*file', content):
            env_issues.append("📁 ENV: File operations without temporary files - may affect file system")
    
    return env_issues

def main():
    try:
        input_data = HookUtils.read_json_input()
        project_dir = HookUtils.get_project_dir()
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only process file operations
        if tool_name not in ["Write", "Edit", "MultiEdit", "Task"]:
            sys.exit(0)
        
        file_path = tool_input.get("filePath", "")
        content = tool_input.get("content", "")
        
        # Skip if no content
        if not content:
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Testing analysis
        coverage_risk, coverage_issues = analyze_test_coverage(content, file_path)
        quality_risk, quality_issues = check_test_quality_patterns(content, file_path)
        doc_issues = validate_test_documentation(content, file_path)
        env_issues = check_test_environment_setup(content, file_path)
        
        # Determine overall risk
        all_risks = [coverage_risk, quality_risk]
        if "HIGH" in all_risks:
            overall_risk = "HIGH"
        elif "MEDIUM" in all_risks or len(env_issues) >= 2:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Block on test anti-patterns
        if quality_risk == "HIGH":
            anti_pattern_details = "\n".join([f"• {issue}" for issue in quality_issues if "ANTI-PATTERN" in issue])
            HookUtils.block_with_error(f"🚫 TEST ANTI-PATTERNS DETECTED\n\n{anti_pattern_details}\n\nFile: {file_path}\n\nFix these anti-patterns to ensure reliable tests.")
        
        # Human confirmation for test quality issues
        if overall_risk == "HIGH" or (overall_risk == "MEDIUM" and quality_risk == "MEDIUM"):
            all_issues = coverage_issues + quality_issues + env_issues
            issue_text = "\n".join([f"• {issue}" for issue in all_issues[:5]])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"🧪 TEST QUALITY REVIEW\n\n{issue_text}\n\nFile: {file_path}\n\nPlease review these testing concerns for quality assurance."
                }
            })
        
        # Success with testing insights
        success_msg = "✅ Test validation completed"
        
        if overall_risk == "MEDIUM" and quality_risk != "HIGH":
            insights = []
            insights.extend([f"💡 {issue}" for issue in coverage_issues[:2]])
            insights.extend([f"💡 {issue}" for issue in quality_issues[:2] if "ANTI-PATTERN" not in issue])
            
            if insights:
                insight_text = "\n".join(insights)
                success_msg += f"\n\nTesting Insights:\n{insight_text}"
        
        all_recommendations = doc_issues + env_issues
        if all_recommendations and overall_risk == "LOW":
            rec_text = "\n".join([f"📋 {rec}" for rec in all_recommendations[:3]])
            success_msg += f"\n\nRecommendations:\n{rec_text}"
        
        is_test_file = any(test_indicator in file_path.lower() for test_indicator in ["test", "spec"])
        suppress_output = (overall_risk == "LOW" and not all_recommendations and not is_test_file)
        
        HookUtils.allow_with_message(success_msg, suppress=suppress_output)
        
    except Exception as e:
        print(f"Testing hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
