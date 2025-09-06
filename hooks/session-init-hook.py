#!/usr/bin/env python3
"""
Session initialization hook - runs at session start
Initializes work status, checks project state, and prepares orchestration
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
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Initialize work status and orchestration files
        work_status.ensure_exists()
        orchestration.ensure_exists()
        
        # Get agent information
        agent_name = os.environ.get("CLAUDE_AGENT_NAME", "unknown-agent")
        timestamp = HookUtils.get_timestamp()
        
        # Log session start
        work_status.log_activity(
            agent=agent_name,
            operation="session_start",
            file_path="",
            status="initialized",
            details=f"Claude Code session initialized at {timestamp}"
        )
        
        # Update orchestration with session start
        orchestration.update_progress(
            agent=agent_name,
            operation="session_initialized",
            file_path="",
            status="active"
        )
        
        # Check if containerization requirements are met
        container_files = []
        project_path = Path(project_dir)
        
        # Look for files that should be containerized
        for pattern in ["*.py", "*.js", "*.ts", "*.go", "*.java"]:
            container_files.extend(project_path.glob(f"**/{pattern}"))
        
        # Check if Dockerfile exists
        dockerfile_exists = any(f.name.lower().startswith("dockerfile") for f in project_path.glob("*"))
        docker_compose_exists = (project_path / "docker-compose.yml").exists() or (project_path / "docker-compose.yaml").exists()
        
        # Signal containerization needs if appropriate
        if container_files and not (dockerfile_exists or docker_compose_exists):
            orchestration.signal_containerization_needed(
                agent=agent_name,
                files=[f.name for f in container_files[:5]]  # Limit to first 5 files
            )
        
        # Success output
        session_info = {
            "agent": agent_name,
            "timestamp": timestamp,
            "project_files": len(container_files),
            "containerization_ready": dockerfile_exists or docker_compose_exists,
            "work_status_initialized": True,
            "orchestration_ready": True
        }
        
        HookUtils.output_json({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "message": f"✅ Session initialized for {agent_name}",
                "sessionInfo": session_info
            }
        })
        
    except Exception as e:
        # Don't fail session start on hook errors
        print(f"Session init hook error: {e}", file=sys.stderr)
        HookUtils.output_json({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "message": f"⚠️ Session initialized with warnings: {e}"
            }
        })

if __name__ == "__main__":
    main()
