#!/usr/bin/env python3
"""
Python-specific hooks for python-pro, python-pro-advanced, django-expert, fastapi-expert
Validates Python code quality, dependencies, virtual environments, and containerization
"""

import json
import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def validate_python_environment(project_dir: str, tool_input: dict) -> tuple[bool, str]:
    """Validate Python environment and dependencies"""
    
    # Check for Python project files
    python_files = ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"]
    has_python_config = any(HookUtils.file_exists(project_dir, f) for f in python_files)
    
    if not has_python_config:
        return False, "🐍 PYTHON PROJECT: Missing dependency file (requirements.txt, pyproject.toml, setup.py, or Pipfile)"
    
    # Check virtual environment recommendations
    file_path = tool_input.get("filePath", tool_input.get("file_path", ""))
    if file_path.endswith(".py"):
        venv_files = [".venv", "venv", ".env"]
        has_venv = any(os.path.exists(os.path.join(project_dir, vf)) for vf in venv_files)
        
        if not has_venv:
            return False, "🐍 VIRTUAL ENVIRONMENT: Python projects should use virtual environments (.venv folder recommended)"
    
    return True, "Python environment validated"

def check_python_code_quality(tool_input: dict) -> tuple[str, str]:
    """Check Python code for common issues"""
    
    content = tool_input.get("content", "")
    file_path = tool_input.get("filePath", tool_input.get("file_path", ""))
    
    if not file_path.endswith(".py"):
        return "LOW", "Non-Python file"
    
    high_risk_patterns = [
        (r"exec\s*\(", "exec() usage detected - security risk"),
        (r"eval\s*\(", "eval() usage detected - security risk"), 
        (r"__import__\s*\(", "Dynamic imports detected - review required"),
        (r"os\.system\s*\(", "os.system() usage - security risk"),
        (r"subprocess\.call.*shell=True", "subprocess with shell=True - security risk"),
        (r"input\s*\(\s*\)", "input() without validation - potential security issue"),
    ]
    
    medium_risk_patterns = [
        (r"DEBUG\s*=\s*True", "DEBUG=True detected - should be False in production"),
        (r"SECRET_KEY\s*=\s*['\"][^'\"]{1,20}['\"]", "Weak SECRET_KEY detected"),
        (r"password\s*=\s*['\"][^'\"]*['\"]", "Hardcoded password detected"),
        (r"api_key\s*=\s*['\"][^'\"]*['\"]", "Hardcoded API key detected"),
    ]
    
    issues = []
    
    for pattern, message in high_risk_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"HIGH RISK: {message}")
    
    if issues:
        return "HIGH", "; ".join(issues)
    
    for pattern, message in medium_risk_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"MEDIUM RISK: {message}")
    
    if issues:
        return "MEDIUM", "; ".join(issues)
    
    return "LOW", "Python code quality check passed"

def check_containerization_requirements(project_dir: str, tool_input: dict) -> tuple[bool, str]:
    """Check if Python service needs containerization"""
    
    content = tool_input.get("content", "")
    file_path = tool_input.get("filePath", tool_input.get("file_path", ""))
    
    # Check for web framework imports
    web_frameworks = [
        "from fastapi import", "import fastapi",
        "from flask import", "import flask", 
        "from django", "import django",
        "from starlette import", "import starlette"
    ]
    
    is_web_service = any(fw in content.lower() for fw in web_frameworks)
    
    if is_web_service:
        # Check for Docker files
        has_dockerfile = HookUtils.file_exists(project_dir, "Dockerfile")
        has_compose = HookUtils.file_exists(project_dir, "docker-compose.yml")
        
        if not has_dockerfile and not has_compose:
            return False, "🐳 CONTAINERIZATION REQUIRED: Python web service detected without Docker configuration"
    
    return True, "Containerization requirements satisfied"

def main():
    try:
        input_data = HookUtils.read_json_input()
        project_dir = HookUtils.get_project_dir()
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only process Python-related tools
        if tool_name not in ["Write", "Edit", "MultiEdit", "Task"]:
            sys.exit(0)
        
        # Skip non-Python files for most checks
        file_path = tool_input.get("filePath", tool_input.get("file_path", ""))
        if file_path and not (file_path.endswith(".py") or "requirements" in file_path or "pyproject" in file_path):
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Validate Python environment
        env_valid, env_msg = validate_python_environment(project_dir, tool_input)
        if not env_valid:
            HookUtils.block_with_error(env_msg)
        
        # Check code quality
        risk_level, risk_msg = check_python_code_quality(tool_input)
        
        # Check containerization
        container_valid, container_msg = check_containerization_requirements(project_dir, tool_input)
        if not container_valid:
            orchestration.signal_containerization_needed("python-agent", [file_path])
            HookUtils.block_with_error(container_msg)
        
        # Human confirmation for high-risk code
        if risk_level == "HIGH":
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"🚨 PYTHON SECURITY REVIEW REQUIRED\n\n{risk_msg}\n\nFile: {file_path}\n\nPlease review this code carefully before proceeding."
                }
            })
        
        # Success message
        success_msg = f"✅ Python validation passed\n{env_msg}\n{container_msg}"
        if risk_level == "MEDIUM":
            success_msg += f"\n⚠️ {risk_msg}"
        
        HookUtils.allow_with_message(success_msg, suppress=risk_level == "LOW")
        
    except Exception as e:
        print(f"Python hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
