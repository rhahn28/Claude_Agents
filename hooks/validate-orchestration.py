#!/usr/bin/env python3
"""
validate-orchestration.py - Enhanced PreToolUse hook with human-in-the-loop feedback
Validates orchestration requirements and provides human confirmation for high-risk operations.
"""

import json
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def assess_risk_level(tool_name: str, tool_input: dict) -> tuple[str, str]:
    """Assess risk level of the operation"""
    
    high_risk_indicators = [
        "production", "prod", "deploy", "delete", "remove", "drop",
        "master", "main", "--force", "--hard", "truncate"
    ]
    
    medium_risk_indicators = [
        "database", "schema", "migration", "config", "settings",
        "docker-compose", "dockerfile", "kubernetes"
    ]
    
    # Analyze tool input for risk indicators
    content_to_check = json.dumps(tool_input).lower()
    
    if any(indicator in content_to_check for indicator in high_risk_indicators):
        return "HIGH", "⚠️  HIGH RISK: Operation affects critical systems or data"
    elif any(indicator in content_to_check for indicator in medium_risk_indicators):
        return "MEDIUM", "🔶 MEDIUM RISK: Operation affects important configurations"
    else:
        return "LOW", "✅ LOW RISK: Standard development operation"

def validate_containerization_requirements(project_dir: str, tool_input: dict) -> tuple[bool, str]:
    """Validate containerization requirements"""
    
    description = tool_input.get("description", "").lower()
    requires_containerization = any(keyword in description for keyword in 
                                   ["deploy", "build", "service", "app", "server", "api"])
    
    if not requires_containerization:
        return True, "No containerization required"
    
    # Check for container files
    dockerfile = Path(project_dir) / "Dockerfile"
    compose_file = Path(project_dir) / "docker-compose.yml"
    
    if not dockerfile.exists() and not compose_file.exists():
        return False, "🐳 CONTAINERIZATION REQUIRED: Missing Dockerfile or docker-compose.yml. This operation requires containerization approval from docker-expert."
    
    return True, "Containerization requirements satisfied"

def validate_orchestration_requirements(project_dir: str, tool_input: dict) -> tuple[bool, str]:
    """Enhanced orchestration validation"""
    
    orchestration_mgr = OrchestrationManager(project_dir)
    work_status_mgr = WorkStatusManager(project_dir)
    
    # Ensure orchestration files exist
    orchestration_mgr.ensure_exists()
    work_status_mgr.ensure_exists()
    
    # Check for file conflicts
    files_to_modify = []
    if "filePath" in tool_input:
        files_to_modify.append(tool_input["filePath"])
    elif "file_path" in tool_input:
        files_to_modify.append(tool_input["file_path"])
    elif "files" in tool_input:
        files_to_modify.extend(tool_input["files"])
    
    # Check locks
    for file_path in files_to_modify:
        is_locked, lock_info = work_status_mgr.is_file_locked(file_path)
        if is_locked:
            return False, f"🔒 FILE CONFLICT: {lock_info}. Coordinate with the locking agent or wait for unlock."
    
    # Validate containerization if needed
    container_valid, container_msg = validate_containerization_requirements(project_dir, tool_input)
    if not container_valid:
        return False, container_msg
    
    return True, "All orchestration requirements validated"

def main():
    try:
        input_data = HookUtils.read_json_input()
        project_dir = HookUtils.get_project_dir()
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only validate specific tools that need orchestration
        orchestration_tools = ["Task", "Write", "Edit", "MultiEdit", "Bash"]
        if tool_name not in orchestration_tools:
            sys.exit(0)
        
        # Assess risk level
        risk_level, risk_message = assess_risk_level(tool_name, tool_input)
        
        # Validate orchestration requirements
        is_valid, validation_message = validate_orchestration_requirements(project_dir, tool_input)
        
        if not is_valid:
            HookUtils.block_with_error(f"""🚫 ORCHESTRATION VALIDATION FAILED

{validation_message}

📋 Required Actions:
1. Ensure orchestration-index.md exists and is current
2. Check WORK_STATUS.md for file locks and conflicts  
3. Follow containerization requirements (docker-expert approval)
4. Coordinate with appropriate agents before proceeding

{risk_message}""")
        
        # Human-in-the-loop for high-risk operations
        if risk_level == "HIGH":
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"""🚨 HUMAN CONFIRMATION REQUIRED

{risk_message}

Operation Details:
- Tool: {tool_name}
- Description: {tool_input.get('description', 'N/A')}
- Risk Assessment: {risk_level}

Please review carefully and confirm this high-risk operation."""
                }
            })
        
        # Success with risk awareness
        success_message = f"✅ Orchestration validated successfully\n{risk_message}\n{validation_message}"
        
        HookUtils.allow_with_message(success_message, suppress=risk_level == "LOW")
        
    except Exception as e:
        print(f"Error: Hook execution failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
