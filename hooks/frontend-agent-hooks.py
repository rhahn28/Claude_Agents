#!/usr/bin/env python3
"""
Frontend-specific hooks for react-pro, vue-expert, angular-expert, frontend-specialist
Validates frontend frameworks, dependencies, build processes, and accessibility
"""

import json
import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def validate_frontend_environment(project_dir: str, tool_input: dict) -> tuple[bool, str]:
    """Validate frontend project structure and dependencies"""
    
    # Check for package.json
    if not HookUtils.file_exists(project_dir, "package.json"):
        file_path = tool_input.get("filePath", "")
        if any(ext in file_path for ext in [".js", ".jsx", ".ts", ".tsx", ".vue"]):
            return False, "🌐 FRONTEND PROJECT: Missing package.json for JavaScript/TypeScript project"
    
    # Check for proper build configuration
    build_files = ["vite.config.js", "webpack.config.js", "next.config.js", "vue.config.js", "angular.json"]
    has_build_config = any(HookUtils.file_exists(project_dir, bf) for bf in build_files)
    
    package_json_content = HookUtils.read_file(project_dir, "package.json")
    if package_json_content and not has_build_config:
        if "build" not in package_json_content:
            return False, "🛠️ BUILD CONFIGURATION: Frontend project missing build configuration"
    
    return True, "Frontend environment validated"

def check_accessibility_compliance(tool_input: dict) -> tuple[str, list]:
    """Check for accessibility issues in frontend code"""
    
    content = tool_input.get("content", "")
    file_path = tool_input.get("filePath", "")
    
    if not any(ext in file_path for ext in [".jsx", ".tsx", ".vue", ".html"]):
        return "LOW", []
    
    accessibility_issues = []
    
    # Check for common accessibility issues
    a11y_patterns = [
        (r"<img(?![^>]*alt=)", "Images without alt attributes"),
        (r"<button(?![^>]*aria-label)(?![^>]*>.*</button>)", "Buttons without accessible labels"),
        (r"<input(?![^>]*aria-label)(?![^>]*id=)", "Form inputs without labels"),
        (r"onClick.*div|onClick.*span", "Non-interactive elements with click handlers"),
        (r"style.*color.*#[0-9a-fA-F]{6}.*background.*#[0-9a-fA-F]{6}", "Potential color contrast issues"),
    ]
    
    for pattern, issue in a11y_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            accessibility_issues.append(issue)
    
    if len(accessibility_issues) >= 3:
        return "HIGH", accessibility_issues
    elif accessibility_issues:
        return "MEDIUM", accessibility_issues
    
    return "LOW", []

def check_frontend_security(tool_input: dict) -> tuple[str, list]:
    """Check for frontend security issues"""
    
    content = tool_input.get("content", "")
    file_path = tool_input.get("filePath", "")
    
    if not any(ext in file_path for ext in [".js", ".jsx", ".ts", ".tsx", ".vue"]):
        return "LOW", []
    
    security_issues = []
    
    # Check for security vulnerabilities
    security_patterns = [
        (r"innerHTML\s*=", "innerHTML usage - XSS risk"),
        (r"dangerouslySetInnerHTML", "dangerouslySetInnerHTML usage - XSS risk"),
        (r"eval\s*\(", "eval() usage - code injection risk"),
        (r"document\.write\s*\(", "document.write() usage - security risk"),
        (r"window\.location\s*=.*\+", "Dynamic window.location - open redirect risk"),
        (r"localStorage\.setItem.*token|sessionStorage\.setItem.*token", "Token storage in localStorage - security risk"),
    ]
    
    for pattern, issue in security_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            security_issues.append(issue)
    
    if len(security_issues) >= 2:
        return "HIGH", security_issues
    elif security_issues:
        return "MEDIUM", security_issues
    
    return "LOW", []

def check_performance_issues(tool_input: dict) -> tuple[str, list]:
    """Check for frontend performance issues"""
    
    content = tool_input.get("content", "")
    file_path = tool_input.get("filePath", "")
    
    performance_issues = []
    
    # Check for performance anti-patterns
    perf_patterns = [
        (r"useEffect\s*\(\s*[^,]*,\s*\[\s*\]", "useEffect with empty dependency array - consider optimization"),
        (r"useState\s*\(\s*.*\.map\(", "useState with map operation - consider useMemo"),
        (r"\.map\s*\([^)]*\)\s*\.map\s*\(", "Chained map operations - performance concern"),
        (r"document\.querySelector.*loop|for.*document\.querySelector", "DOM queries in loops"),
    ]
    
    for pattern, issue in perf_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            performance_issues.append(issue)
    
    if len(performance_issues) >= 2:
        return "MEDIUM", performance_issues
    elif performance_issues:
        return "LOW", performance_issues
    
    return "LOW", []

def main():
    try:
        input_data = HookUtils.read_json_input()
        project_dir = HookUtils.get_project_dir()
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only process frontend-related tools
        if tool_name not in ["Write", "Edit", "MultiEdit", "Task"]:
            sys.exit(0)
        
        # Check if this is frontend-related
        file_path = tool_input.get("filePath", "")
        frontend_extensions = [".js", ".jsx", ".ts", ".tsx", ".vue", ".html", ".css", ".scss", ".json"]
        if file_path and not any(ext in file_path for ext in frontend_extensions):
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Validate frontend environment
        env_valid, env_msg = validate_frontend_environment(project_dir, tool_input)
        if not env_valid:
            HookUtils.block_with_error(env_msg)
        
        # Check accessibility
        a11y_level, a11y_issues = check_accessibility_compliance(tool_input)
        
        # Check security
        security_level, security_issues = check_frontend_security(tool_input)
        
        # Check performance
        perf_level, perf_issues = check_performance_issues(tool_input)
        
        # Determine overall risk level
        all_levels = [a11y_level, security_level, perf_level]
        if "HIGH" in all_levels:
            overall_risk = "HIGH"
        elif "MEDIUM" in all_levels:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Compile all issues
        all_issues = []
        if a11y_issues:
            all_issues.extend([f"♿ ACCESSIBILITY: {issue}" for issue in a11y_issues])
        if security_issues:
            all_issues.extend([f"🔒 SECURITY: {issue}" for issue in security_issues])
        if perf_issues:
            all_issues.extend([f"⚡ PERFORMANCE: {issue}" for issue in perf_issues])
        
        # Human confirmation for high-risk issues
        if overall_risk == "HIGH":
            issue_text = "\n".join([f"• {issue}" for issue in all_issues])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask", 
                    "permissionDecisionReason": f"🚨 FRONTEND CODE REVIEW REQUIRED\n\n{issue_text}\n\nFile: {file_path}\n\nPlease review these issues before proceeding."
                }
            })
        
        # Success message with warnings
        success_msg = f"✅ Frontend validation passed\n{env_msg}"
        if overall_risk == "MEDIUM" and all_issues:
            warning_text = "\n".join([f"⚠️ {issue}" for issue in all_issues[:3]])  # Show top 3
            success_msg += f"\n\nWarnings:\n{warning_text}"
        
        HookUtils.allow_with_message(success_msg, suppress=overall_risk == "LOW")
        
    except Exception as e:
        print(f"Frontend hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
