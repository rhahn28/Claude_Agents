#!/usr/bin/env python3
"""
Core hook utilities and shared functions for the Claude Code hooks system.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import subprocess
import re

class HookUtils:
    """Shared utilities for all hooks"""
    
    @staticmethod
    def get_project_dir() -> str:
        """Get the project directory from environment"""
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
        if not project_dir:
            raise ValueError("CLAUDE_PROJECT_DIR environment variable not set")
        return project_dir
    
    @staticmethod
    def read_json_input() -> dict:
        """Read and parse JSON input from stdin"""
        try:
            return json.load(sys.stdin)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON input: {e}")
    
    @staticmethod
    def output_json(data: dict):
        """Output JSON response and exit successfully"""
        print(json.dumps(data, indent=2))
        sys.exit(0)
    
    @staticmethod
    def block_with_error(reason: str, hook_event: str = "PreToolUse"):
        """Block operation with error message"""
        output = {
            "hookSpecificOutput": {
                "hookEventName": hook_event,
                "permissionDecision": "deny" if hook_event == "PreToolUse" else None,
                "permissionDecisionReason": reason
            },
            "decision": "block",
            "reason": reason
        }
        HookUtils.output_json(output)
    
    @staticmethod
    def allow_with_message(message: str, hook_event: str = "PreToolUse", suppress: bool = True):
        """Allow operation with success message"""
        output = {
            "hookSpecificOutput": {
                "hookEventName": hook_event,
                "permissionDecision": "allow" if hook_event == "PreToolUse" else None,
                "permissionDecisionReason": message
            },
            "suppressOutput": suppress
        }
        HookUtils.output_json(output)
    
    @staticmethod
    def get_timestamp() -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    @staticmethod
    def get_agent_from_context(tool_input: dict) -> str:
        """Extract agent name from tool input context"""
        description = tool_input.get("description", "").lower()
        
        agent_keywords = {
            "api-designer": ["api", "openapi", "swagger", "endpoint"],
            "python-pro": ["python", "django", "fastapi", "flask"],
            "react-pro": ["react", "jsx", "component", "frontend"],
            "docker-expert": ["docker", "container", "dockerfile", "compose"],
            "backend-architect": ["backend", "server", "database", "architecture"],
            "devops-engineer": ["deploy", "ci/cd", "pipeline", "infrastructure"],
            "frontend-specialist": ["frontend", "ui", "css", "html"],
            "security-auditor": ["security", "auth", "encryption", "vulnerability"],
            "database-architect": ["database", "schema", "sql", "migration"],
            "test-engineer": ["test", "testing", "pytest", "junit"],
        }
        
        for agent, keywords in agent_keywords.items():
            if any(keyword in description for keyword in keywords):
                return agent
                
        return "system-agent"
    
    @staticmethod
    def get_relative_path(file_path: str, project_dir: str) -> str:
        """Get relative path from project directory"""
        try:
            return str(Path(file_path).relative_to(project_dir))
        except ValueError:
            return file_path
    
    @staticmethod
    def file_exists(project_dir: str, filename: str) -> bool:
        """Check if file exists in project"""
        return (Path(project_dir) / filename).exists()
    
    @staticmethod
    def read_file(project_dir: str, filename: str) -> str:
        """Read file content"""
        try:
            with open(Path(project_dir) / filename, 'r') as f:
                return f.read()
        except Exception:
            return ""
    
    @staticmethod
    def write_file(project_dir: str, filename: str, content: str):
        """Write content to file"""
        file_path = Path(project_dir) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
    
    @staticmethod
    def append_to_file(project_dir: str, filename: str, content: str):
        """Append content to file"""
        file_path = Path(project_dir) / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'a') as f:
            f.write(content)
    
    @staticmethod
    def human_confirmation_required(message: str, details: str = "") -> bool:
        """Check if human confirmation is required based on risk assessment"""
        high_risk_patterns = [
            r"delete|remove|rm\s",
            r"drop\s+table|truncate",
            r"--force|--hard",
            r"production|prod",
            r"master|main.*merge",
            r"deploy.*production"
        ]
        
        combined_text = f"{message} {details}".lower()
        return any(re.search(pattern, combined_text) for pattern in high_risk_patterns)

class WorkStatusManager:
    """Manages WORK_STATUS.md file operations"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.file_path = Path(project_dir) / "WORK_STATUS.md"
    
    def ensure_exists(self):
        """Create WORK_STATUS.md if it doesn't exist"""
        if not self.file_path.exists():
            content = """# Work Status

This file tracks agent activities and file locks to prevent conflicts.

## File Locks
<!-- Active file locks will be listed here -->

## Recent Activities  
<!-- Agent activities will be logged here -->

"""
            HookUtils.write_file(self.project_dir, "WORK_STATUS.md", content)
    
    def is_file_locked(self, file_path: str) -> Tuple[bool, str]:
        """Check if file is locked by another agent"""
        if not self.file_path.exists():
            return False, ""
        
        content = HookUtils.read_file(self.project_dir, "WORK_STATUS.md")
        relative_path = HookUtils.get_relative_path(file_path, self.project_dir)
        
        for line in content.split('\n'):
            if line.strip().startswith("LOCKED:") and relative_path in line:
                return True, line.strip()
        
        return False, ""
    
    def lock_file(self, file_path: str, agent: str, operation: str = "editing"):
        """Lock a file for exclusive access"""
        self.ensure_exists()
        relative_path = HookUtils.get_relative_path(file_path, self.project_dir)
        timestamp = HookUtils.get_timestamp()
        
        lock_entry = f"LOCKED: `{relative_path}` by {agent} ({operation}) at {timestamp}\n"
        
        # Remove existing locks for this file
        self.unlock_file(file_path, silent=True)
        
        # Add new lock
        content = HookUtils.read_file(self.project_dir, "WORK_STATUS.md")
        if "## File Locks" in content:
            content = content.replace("## File Locks\n<!-- Active file locks will be listed here -->", 
                                    f"## File Locks\n<!-- Active file locks will be listed here -->\n{lock_entry}")
        else:
            content += f"\n{lock_entry}"
        
        HookUtils.write_file(self.project_dir, "WORK_STATUS.md", content)
    
    def unlock_file(self, file_path: str, silent: bool = False):
        """Unlock a file"""
        if not self.file_path.exists():
            return
        
        relative_path = HookUtils.get_relative_path(file_path, self.project_dir)
        content = HookUtils.read_file(self.project_dir, "WORK_STATUS.md")
        
        lines = content.split('\n')
        filtered_lines = [line for line in lines if not (line.strip().startswith("LOCKED:") and relative_path in line)]
        
        if len(filtered_lines) != len(lines):
            HookUtils.write_file(self.project_dir, "WORK_STATUS.md", '\n'.join(filtered_lines))
    
    def log_activity(self, agent: str, operation: str, file_path: str, status: str, details: str = ""):
        """Log agent activity"""
        self.ensure_exists()
        timestamp = HookUtils.get_timestamp()
        relative_path = HookUtils.get_relative_path(file_path, self.project_dir)
        
        entry = f"""
## {timestamp} - {operation.upper()}
- **Agent**: {agent}
- **File**: `{relative_path}`
- **Status**: {status}
{f"- **Details**: {details}" if details else ""}
"""
        
        content = HookUtils.read_file(self.project_dir, "WORK_STATUS.md")
        
        # Insert after "Recent Activities" section
        if "## Recent Activities" in content:
            content = content.replace("## Recent Activities\n<!-- Agent activities will be logged here -->", 
                                    f"## Recent Activities\n<!-- Agent activities will be logged here -->{entry}")
        else:
            content += entry
        
        # Keep only last 20 activities
        self._trim_activities(content)
    
    def _trim_activities(self, content: str):
        """Keep only the most recent activities"""
        lines = content.split('\n')
        activity_count = sum(1 for line in lines if re.match(r'## \d{4}-\d{2}-\d{2}', line))
        
        if activity_count > 20:
            # Keep header and first 15 activities
            keep_lines = []
            activity_seen = 0
            for line in lines:
                if re.match(r'## \d{4}-\d{2}-\d{2}', line):
                    activity_seen += 1
                    if activity_seen > 15:
                        break
                keep_lines.append(line)
            
            content = '\n'.join(keep_lines) + "\n\n<!-- Older activities trimmed -->"
        
        HookUtils.write_file(self.project_dir, "WORK_STATUS.md", content)

class OrchestrationManager:
    """Manages orchestration-index.md operations"""
    
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.file_path = Path(project_dir) / "orchestration-index.md"
    
    def ensure_exists(self):
        """Create orchestration-index.md if it doesn't exist"""
        if not self.file_path.exists():
            content = """# Orchestration Index

This file coordinates multi-agent development activities and tracks project progress.

## Project Context
<!-- Project overview and requirements -->

## Agent Coordination
<!-- Inter-agent dependencies and communication -->

## Current Status
<!-- Active work streams and progress -->

## Containerization Status
<!-- Docker and deployment readiness -->

"""
            HookUtils.write_file(self.project_dir, "orchestration-index.md", content)
    
    def update_progress(self, agent: str, operation: str, file_path: str, status: str):
        """Update orchestration progress"""
        self.ensure_exists()
        timestamp = HookUtils.get_timestamp()
        relative_path = HookUtils.get_relative_path(file_path, self.project_dir)
        
        progress_entry = f"""
### Latest Progress ({timestamp})
- **Agent**: {agent}
- **Operation**: {operation}
- **File**: `{relative_path}`
- **Status**: {status}

"""
        
        content = HookUtils.read_file(self.project_dir, "orchestration-index.md")
        
        # Remove previous "Latest Progress" section
        lines = content.split('\n')
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            if line.startswith("### Latest Progress"):
                skip_section = True
                continue
            elif line.startswith("###") or line.startswith("##"):
                if skip_section:
                    skip_section = False
                    filtered_lines.append(line)
            elif not skip_section:
                filtered_lines.append(line)
            elif skip_section and line.strip() == "":
                continue
        
        content = '\n'.join(filtered_lines) + progress_entry
        HookUtils.write_file(self.project_dir, "orchestration-index.md", content)
    
    def signal_containerization_needed(self, agent: str, files: List[str]):
        """Signal that containerization review is needed"""
        self.ensure_exists()
        timestamp = HookUtils.get_timestamp()
        
        container_alert = f"""
### 🐳 CONTAINERIZATION REVIEW REQUIRED ({timestamp})
- **Requested by**: {agent}
- **Files needing containerization**: {', '.join([f"`{f}`" for f in files])}
- **Status**: PENDING docker-expert review
- **Action Required**: docker-expert must review and approve containerization

"""
        
        content = HookUtils.read_file(self.project_dir, "orchestration-index.md")
        
        # Add to containerization status section
        if "## Containerization Status" in content:
            content = content.replace("## Containerization Status\n<!-- Docker and deployment readiness -->", 
                                    f"## Containerization Status\n<!-- Docker and deployment readiness -->{container_alert}")
        
        HookUtils.write_file(self.project_dir, "orchestration-index.md", content)
