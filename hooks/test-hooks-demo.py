#!/usr/bin/env python3
"""
Test the demo hooks by simulating Claude Code input
This shows exactly what happens when hooks run
"""

import json
import subprocess
import sys
import os
from pathlib import Path

def test_prewrite_hook():
    """Test the PreToolUse Write hook"""
    
    print("🧪 TESTING PreToolUse Write Hook...")
    print("=" * 50)
    
    # Simulate Claude Code input for a Write operation
    test_input = {
        "session_id": "test-session-123",
        "transcript_path": "/fake/path/conversation.jsonl",
        "cwd": os.getcwd(),
        "hook_event_name": "PreToolUse", 
        "tool_name": "Write",
        "tool_input": {
            "filePath": "test-api.py",
            "content": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello World'}"
        }
    }
    
    # Set the environment variable
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(Path.cwd())
    
    try:
        # Run the hook script
        hook_path = Path(__file__).parent / "demo-write-hook.py"
        process = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(test_input),
            text=True,
            capture_output=True,
            env=env
        )
        
        print(f"📥 INPUT to hook:")
        print(json.dumps(test_input, indent=2))
        print()
        
        print(f"📤 OUTPUT from hook:")
        print(f"Exit Code: {process.returncode}")
        
        if process.stdout:
            try:
                output = json.loads(process.stdout)
                print("JSON Response:")
                print(json.dumps(output, indent=2))
            except:
                print("Raw stdout:", process.stdout)
        
        if process.stderr:
            print("stderr:", process.stderr)
        
        print()
        
        # Check if log file was created
        log_file = Path("hooks-demo.log")
        if log_file.exists():
            print("📝 LOG FILE CONTENT:")
            print(log_file.read_text())
        
        return process.returncode == 0
        
    except Exception as e:
        print(f"❌ Error testing hook: {e}")
        return False

def test_postwrite_hook():
    """Test the PostToolUse Write hook"""
    
    print("\n🧪 TESTING PostToolUse Write Hook...")
    print("=" * 50)
    
    # Simulate Claude Code input after Write completes
    test_input = {
        "session_id": "test-session-123", 
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {
            "filePath": "test-api.py",
            "content": "from fastapi import FastAPI..."
        },
        "tool_response": {
            "filePath": "test-api.py",
            "success": True
        }
    }
    
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(Path.cwd())
    
    try:
        hook_path = Path(__file__).parent / "demo-post-write-hook.py" 
        process = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(test_input),
            text=True,
            capture_output=True,
            env=env
        )
        
        print(f"📥 INPUT to post-hook:")
        print(json.dumps(test_input, indent=2))
        print()
        
        print(f"📤 POST-HOOK RESULT:")
        print(f"Exit Code: {process.returncode}")
        
        if process.stdout:
            print("stdout:", process.stdout)
        if process.stderr:
            print("stderr:", process.stderr)
        
        # Check status file
        status_file = Path("WORK_STATUS.md")
        if status_file.exists():
            print("\n📊 WORK_STATUS.md UPDATED:")
            print(status_file.read_text()[-300:])  # Last 300 chars
        
        return process.returncode == 0
        
    except Exception as e:
        print(f"❌ Error testing post-hook: {e}")
        return False

def main():
    print("🚀 CLAUDE CODE HOOKS DEMONSTRATION")
    print("This shows exactly how hooks intercept and process Claude Code operations")
    print()
    
    # Test both hooks
    pre_success = test_prewrite_hook()
    post_success = test_postwrite_hook()
    
    print("\n" + "=" * 60)
    print("🏆 DEMONSTRATION RESULTS:")
    print(f"PreToolUse Hook:  {'✅ SUCCESS' if pre_success else '❌ FAILED'}")
    print(f"PostToolUse Hook: {'✅ SUCCESS' if post_success else '❌ FAILED'}")
    
    if pre_success and post_success:
        print("\n🎉 Hooks are working correctly!")
        print("In real Claude Code, these would:")
        print("  • Block/allow operations before they run")
        print("  • Update tracking files automatically")
        print("  • Provide human-in-the-loop confirmations")
        print("  • Enforce containerization requirements")
    else:
        print("\n⚠️ Some hooks failed - check the error messages above")

if __name__ == "__main__":
    main()
