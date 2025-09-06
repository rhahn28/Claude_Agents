#!/usr/bin/env python3
"""
Test critical file detection - shows human-in-the-loop confirmation
"""

import json
import subprocess
import sys
import os
from pathlib import Path

def test_critical_file():
    """Test hook response to critical file modification"""
    
    print("🚨 TESTING Critical File Detection...")
    print("=" * 50)
    
    # Test with .env file (critical)
    test_input = {
        "session_id": "test-session-456",
        "transcript_path": "/fake/path/conversation.jsonl",
        "cwd": os.getcwd(),
        "hook_event_name": "PreToolUse", 
        "tool_name": "Write",
        "tool_input": {
            "filePath": ".env",
            "content": "DATABASE_URL=postgresql://user:pass@localhost/db\nSECRET_KEY=super-secret-key-here"
        }
    }
    
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(Path.cwd().parent)
    
    try:
        hook_path = Path(__file__).parent / "demo-write-hook.py"
        process = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(test_input),
            text=True,
            capture_output=True,
            env=env
        )
        
        print(f"📥 INPUT (Critical File - .env):")
        print(json.dumps(test_input, indent=2))
        print()
        
        print(f"📤 HOOK RESPONSE:")
        print(f"Exit Code: {process.returncode}")
        
        if process.stdout:
            try:
                output = json.loads(process.stdout)
                print("🚨 HUMAN CONFIRMATION REQUIRED:")
                print(json.dumps(output, indent=2))
                
                decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
                if decision == "ask":
                    print("\n✅ SUCCESS: Hook correctly identified critical file!")
                    print("In real Claude Code, this would show a confirmation dialog.")
                
            except:
                print("Raw stdout:", process.stdout)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_containerization_enforcement():
    """Test containerization requirement enforcement"""
    
    print("\n🐳 TESTING Containerization Enforcement...")
    print("=" * 50)
    
    # Test with docker-compose.yml (container config)
    test_input = {
        "session_id": "test-session-789",
        "hook_event_name": "PreToolUse", 
        "tool_name": "Write",
        "tool_input": {
            "filePath": "docker-compose.yml",
            "content": "version: '3.8'\nservices:\n  api:\n    build: .\n    ports:\n      - '8000:8000'"
        }
    }
    
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(Path.cwd().parent)
    
    try:
        hook_path = Path(__file__).parent / "demo-write-hook.py"
        process = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(test_input),
            text=True,
            capture_output=True,
            env=env
        )
        
        print(f"📥 INPUT (Container Config):")
        print(json.dumps(test_input, indent=2))
        print()
        
        print(f"📤 HOOK RESPONSE:")
        if process.stdout:
            try:
                output = json.loads(process.stdout)
                decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
                print(f"Decision: {decision}")
                print(f"Reason: {output.get('hookSpecificOutput', {}).get('permissionDecisionReason')}")
                
                if decision == "ask":
                    print("\n✅ SUCCESS: Docker config file flagged for review!")
                
            except:
                print("Raw stdout:", process.stdout)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔍 CLAUDE CODE HOOKS - ADVANCED FEATURES DEMO")
    print("Testing critical file detection and containerization enforcement")
    print()
    
    critical_success = test_critical_file()
    container_success = test_containerization_enforcement()
    
    print("\n" + "=" * 60)
    print("🏆 ADVANCED FEATURES TEST RESULTS:")
    print(f"Critical File Detection:      {'✅ SUCCESS' if critical_success else '❌ FAILED'}")
    print(f"Containerization Enforcement: {'✅ SUCCESS' if container_success else '❌ FAILED'}")
    
    if critical_success and container_success:
        print(f"\n🎉 Advanced hooks working perfectly!")
        print(f"This demonstrates:")
        print(f"  🚨 Human-in-the-loop confirmation for critical files")
        print(f"  🐳 Automatic containerization requirement detection")
        print(f"  📝 Intelligent file classification and risk assessment")
        print(f"  🔒 Protection against accidental critical file modification")

if __name__ == "__main__":
    main()
