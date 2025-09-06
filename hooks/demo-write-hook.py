#!/usr/bin/env python3
"""
Simple test hook to demonstrate how Claude Code hooks work
This will run on PreToolUse for Write operations
"""

import json
import sys
import os
from datetime import datetime

def main():
    try:
        # Read JSON input from Claude Code
        input_data = json.load(sys.stdin)
        
        # Extract information
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        session_id = input_data.get("session_id", "")
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
        
        # Only process Write tool
        if tool_name != "Write":
            sys.exit(0)
        
        # Get file information
        file_path = tool_input.get("filePath", "")
        content_preview = tool_input.get("content", "")[:100] + "..." if len(tool_input.get("content", "")) > 100 else tool_input.get("content", "")
        
        # Log the operation
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"\n[{timestamp}] HOOK INTERCEPTED Write operation:\n"
        log_entry += f"  - File: {file_path}\n"
        log_entry += f"  - Content preview: {content_preview}\n"
        log_entry += f"  - Session: {session_id}\n"
        
        # Write to log file
        if project_dir:
            log_file = os.path.join(project_dir, "hooks-demo.log")
            with open(log_file, "a") as f:
                f.write(log_entry)
        
        # Check if this is a critical file
        critical_files = [".env", "settings.json", "docker-compose.yml"]
        is_critical = any(cf in file_path.lower() for cf in critical_files)
        
        if is_critical:
            # Ask human for confirmation on critical files
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"🚨 CRITICAL FILE DETECTED\n\nYou're about to modify: {file_path}\n\nThis is a critical configuration file. Please confirm you want to proceed.\n\nContent preview:\n{content_preview}"
                }
            }
            print(json.dumps(output))
            sys.exit(0)
        
        # Allow normal files with a success message
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": f"✅ File operation validated - writing to {os.path.basename(file_path)}"
            },
            "suppressOutput": True
        }
        print(json.dumps(output))
        sys.exit(0)
        
    except Exception as e:
        # Error handling
        error_msg = f"Hook error: {str(e)}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
