#!/usr/bin/env python3
"""
Orchestration sync hook - runs after file operations to update work status
Manages file locking, coordination signals, and work status synchronization
"""

import json
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def main():
    try:
        input_data = HookUtils.read_json_input()
        project_dir = HookUtils.get_project_dir()
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        tool_output = input_data.get("tool_output", {})
        
        # Only process file operations
        if tool_name not in ["Write", "Edit", "MultiEdit"]:
            sys.exit(0)
        
        file_path = tool_input.get("filePath", "")
        if not file_path:
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Update work status
        agent_name = os.environ.get("CLAUDE_AGENT_NAME", "unknown-agent")
        operation = f"{tool_name} operation on {os.path.basename(file_path)}"
        
        work_status.log_activity(
            agent=agent_name,
            operation=operation,
            file_path=file_path,
            status="completed"
        )
        
        # Release any file locks
        work_status.unlock_file(file_path)
        
        # Signal completion to dependent agents
        if tool_name in ["Write", "Edit"]:
            # Determine which agents might be interested
            dependent_agents = []
            
            # File type based dependencies
            if file_path.endswith(('.py', '.pyi')):
                dependent_agents.extend(['test-automation-expert', 'security-auditor'])
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                dependent_agents.extend(['test-automation-expert', 'ui-ux-designer'])
            elif file_path.endswith(('.sql', '.py')) and 'model' in file_path.lower():
                dependent_agents.extend(['database-expert', 'security-auditor'])
            elif file_path.endswith(('.yml', '.yaml', '.dockerfile')):
                dependent_agents.extend(['docker-expert', 'security-auditor'])
            elif file_path.endswith(('.md', '.rst', '.txt')):
                dependent_agents.extend(['technical-writer'])
            
            # Signal dependent agents - log coordination needs
            for dep_agent in dependent_agents:
                orchestration.update_progress(dep_agent, "coordination_signal", file_path, "pending_review")
        
        # Update orchestration index with completion
        orchestration.update_progress(agent_name, operation, file_path, "completed")
        
        # Success output
        HookUtils.output_json({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "message": f"✅ Orchestration sync completed for {os.path.basename(file_path)}"
            }
        })
        
    except Exception as e:
        print(f"Orchestration sync hook error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't fail the operation for sync errors

if __name__ == "__main__":
    main()
