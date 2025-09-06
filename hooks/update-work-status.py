#!/usr/bin/env python3
"""
update-work-status.py - PostToolUse hook for Write/Edit/MultiEdit tools
Automatically updates WORK_STATUS.md after file operations to track agent activities.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

def update_work_status(project_dir: str, tool_name: str, tool_input: dict, tool_response: dict):
    """
    Update WORK_STATUS.md with the latest file operation information.
    """
    work_status_file = Path(project_dir) / "WORK_STATUS.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extract file information from tool input/response
    file_path = tool_input.get("filePath", tool_input.get("file_path", ""))
    if not file_path:
        return "No file path found in tool input"
    
    # Get relative path for cleaner display
    try:
        relative_path = Path(file_path).relative_to(project_dir)
    except ValueError:
        relative_path = file_path
    
    # Determine operation type and status
    operation = tool_name.upper()
    success = tool_response.get("success", True)
    status = "✅ COMPLETED" if success else "❌ FAILED"
    
    # Create or update WORK_STATUS.md
    try:
        if work_status_file.exists():
            with open(work_status_file, 'r') as f:
                content = f.read()
        else:
            content = "# Work Status\\n\\nThis file tracks agent activities and file locks to prevent conflicts.\\n\\n"
        
        # Add new entry
        entry = f"\\n## {timestamp} - {operation} Operation\\n"
        entry += f"- **File**: `{relative_path}`\\n"
        entry += f"- **Status**: {status}\\n"
        entry += f"- **Agent**: {get_current_agent()}\\n"
        
        # Remove any existing locks for this file if operation succeeded
        if success and "LOCKED:" in content:
            lines = content.split('\\n')
            filtered_lines = []
            for line in lines:
                if not (line.strip().startswith("LOCKED:") and str(relative_path) in line):
                    filtered_lines.append(line)
            content = '\\n'.join(filtered_lines)
        
        # Append new entry
        content += entry
        
        # Keep only last 50 entries to prevent file from growing too large
        lines = content.split('\\n')
        if len([l for l in lines if l.startswith("## ")]) > 50:
            # Find the 40th entry and truncate there
            entry_count = 0
            truncate_index = 0
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    entry_count += 1
                    if entry_count == 40:
                        truncate_index = i
                        break
            if truncate_index > 0:
                lines = lines[:truncate_index] + ["\\n## ... (older entries truncated) ...\\n"]
            content = '\\n'.join(lines)
        
        # Write updated content
        with open(work_status_file, 'w') as f:
            f.write(content)
            
        return f"Updated WORK_STATUS.md with {operation} operation on {relative_path}"
        
    except Exception as e:
        return f"Error updating WORK_STATUS.md: {str(e)}"

def get_current_agent():
    """
    Try to determine which agent is currently active based on context.
    """
    # This is a simplified version - in practice, you might parse the session
    # or use other context to determine the active agent
    return "system-agent"

def update_orchestration_index(project_dir: str, file_path: str, operation: str):
    """
    Update orchestration-index.md with progress information.
    """
    orchestration_file = Path(project_dir) / "orchestration-index.md"
    if not orchestration_file.exists():
        return "orchestration-index.md not found"
        
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(orchestration_file, 'r') as f:
            content = f.read()
        
        # Add progress entry at the end
        progress_entry = f"\\n### Latest Activity ({timestamp})\\n"
        progress_entry += f"- **Operation**: {operation}\\n"
        progress_entry += f"- **File**: `{file_path}`\\n"
        progress_entry += f"- **Status**: Completed\\n\\n"
        
        # Remove previous "Latest Activity" section if exists
        lines = content.split('\\n')
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            if line.startswith("### Latest Activity"):
                skip_section = True
                continue
            elif line.startswith("###") or line.startswith("##"):
                skip_section = False
                
            if not skip_section:
                filtered_lines.append(line)
        
        content = '\\n'.join(filtered_lines)
        content += progress_entry
        
        with open(orchestration_file, 'w') as f:
            f.write(content)
            
        return "Updated orchestration-index.md with latest activity"
        
    except Exception as e:
        return f"Error updating orchestration-index.md: {str(e)}"

def main():
    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        tool_response = input_data.get("tool_response", {})
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
        
        # Only process file operation tools
        if tool_name not in ["Write", "Edit", "MultiEdit"]:
            sys.exit(0)
            
        if not project_dir:
            print("CLAUDE_PROJECT_DIR environment variable not set", file=sys.stderr)
            sys.exit(1)
        
        # Update work status
        work_status_result = update_work_status(project_dir, tool_name, tool_input, tool_response)
        
        # Update orchestration index
        file_path = tool_input.get("filePath", tool_input.get("file_path", ""))
        orchestration_result = update_orchestration_index(project_dir, file_path, tool_name)
        
        # Output success message
        message = f"📝 Automatically updated tracking files:\\n- {work_status_result}\\n- {orchestration_result}"
        print(message, file=sys.stderr)  # Show to user in debug mode
        
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Hook execution failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
