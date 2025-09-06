#!/usr/bin/env python3
"""
Post-hook demo - runs after Write operations complete
"""

import json
import sys
import os
from datetime import datetime

def main():
    try:
        input_data = json.load(sys.stdin)
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        tool_response = input_data.get("tool_response", {})
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
        
        if tool_name != "Write":
            sys.exit(0)
        
        file_path = tool_input.get("filePath", "")
        success = tool_response.get("success", True)
        
        # Log the completion
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if success else "FAILED"
        
        log_entry = f"[{timestamp}] WRITE COMPLETED: {status}\n"
        log_entry += f"  - File: {file_path}\n"
        log_entry += f"  - Response: {tool_response}\n\n"
        
        if project_dir:
            log_file = os.path.join(project_dir, "hooks-demo.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        
        # Update a simple status file
        if project_dir and success:
            status_file = os.path.join(project_dir, "WORK_STATUS.md")
            status_entry = f"\n## {timestamp} - Write Operation\n"
            status_entry += f"- **File**: `{os.path.basename(file_path)}`\n"
            status_entry += f"- **Status**: Completed Successfully\n"
            
            try:
                with open(status_file, "a", encoding="utf-8") as f:
                    f.write(status_entry)
            except:
                # Create if doesn't exist
                with open(status_file, "w", encoding="utf-8") as f:
                    f.write("# Work Status\n\nAgent activities tracked by hooks:\n" + status_entry)
        
        # Success - no output needed for PostToolUse
        sys.exit(0)
        
    except Exception as e:
        print(f"Post-hook error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
