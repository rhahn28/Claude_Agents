# Claude Code Hooks - Real World Example

## How The Hooks System Will Work

### Scenario: Agent writes a new Python file

**When Claude Code executes:** `Write tool with filePath="src/api.py"`

### 1. PreToolUse Hook Triggers BEFORE Write

**Input to hook (JSON via stdin):**
```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/conversation.jsonl", 
  "cwd": "/project/root",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "filePath": "src/api.py",
    "content": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello World'}"
  }
}
```

**Hook Script Processing:**
1. ✅ Validates orchestration requirements
2. 🔍 Checks if `src/api.py` is locked in WORK_STATUS.md  
3. 🐳 Detects this creates an API service → requires containerization
4. ❗ Finds no Dockerfile → BLOCKS operation

**Hook Output (JSON to stdout):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "🐳 CONTAINERIZATION REQUIRED: Missing Dockerfile for API service"
  },
  "decision": "block",
  "reason": "API services must be containerized. Contact docker-expert for Dockerfile creation."
}
```

**Result:** ❌ Write operation BLOCKED, Claude sees the error message

---

### 2. After Docker Expert Creates Dockerfile

**Second attempt - PreToolUse Hook:**
1. ✅ Validates orchestration requirements  
2. ✅ Checks file locks - none found
3. ✅ Finds Dockerfile exists → containerization satisfied
4. ⚠️ Detects "api.py" as critical → human confirmation needed

**Hook Output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse", 
    "permissionDecision": "ask",
    "permissionDecisionReason": "🚨 CRITICAL FILE: Creating new API endpoint. Please confirm this API design."
  }
}
```

**Result:** 🤔 Claude Code shows confirmation dialog to user

---

### 3. User Confirms → Write Proceeds

**Operation succeeds, PostToolUse Hook Triggers AFTER Write**

**Input to post-hook:**
```json
{
  "session_id": "abc123", 
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "filePath": "src/api.py",
    "content": "..."
  },
  "tool_response": {
    "filePath": "src/api.py",
    "success": true
  }
}
```

**Post-Hook Actions:**
1. 📝 Updates WORK_STATUS.md with operation log
2. 🔄 Updates orchestration-index.md with progress  
3. 🐳 Signals docker-expert that new service needs review
4. 📊 Logs activity for audit trail

**Files Created/Updated:**
- ✅ `src/api.py` (the original file)
- ✅ `WORK_STATUS.md` (automatic tracking)
- ✅ `orchestration-index.md` (progress update)
- ✅ `hooks-demo.log` (detailed audit log)

---

### 4. Complete Workflow Visualization

```
User Request: "Create a FastAPI endpoint"
           ↓
Claude Code: Write("src/api.py", content)
           ↓
PreToolUse Hook: validate-orchestration.py
           ↓
❌ BLOCKS: "No Dockerfile found"
           ↓ 
Claude: "Need containerization - calling docker-expert"
           ↓
docker-expert creates Dockerfile  
           ↓
Claude Code: Write("src/api.py", content) [retry]
           ↓
PreToolUse Hook: validate-orchestration.py
           ↓
⚠️ ASKS: "Confirm critical API file creation"
           ↓
User: ✅ Confirms
           ↓
Write Operation EXECUTES
           ↓
PostToolUse Hook: update-work-status.py
           ↓
📝 Updates tracking files automatically
           ↓
✅ COMPLETE: Orchestrated, containerized, tracked
```

---

### 5. Real Files After Hook Execution

**WORK_STATUS.md:**
```markdown
# Work Status

## 2025-08-21 14:23:15 - WRITE Operation
- **Agent**: python-pro
- **File**: `src/api.py` 
- **Status**: ✅ COMPLETED
- **Details**: FastAPI service created with containerization

## Containerization Review Required
🐳 **PENDING**: docker-expert review for src/api.py service
```

**orchestration-index.md:**
```markdown  
# Orchestration Index

### Latest Progress (2025-08-21 14:23:15)
- **Agent**: python-pro
- **Operation**: Write
- **File**: `src/api.py`
- **Status**: Completed - API service containerized
```

**hooks-demo.log:**
```
[2025-08-21 14:23:10] HOOK INTERCEPTED Write operation:
  - File: src/api.py
  - Content preview: from fastapi import FastAPI...
  - Validation: PASSED (containerization satisfied)
  
[2025-08-21 14:23:15] WRITE COMPLETED: ✅ SUCCESS
  - File: src/api.py  
  - Automatic tracking updated
```

---

## Key Benefits Demonstrated:

🚫 **Prevents Mistakes**: Blocked non-containerized deployment
🤔 **Human Oversight**: Asked for confirmation on critical files  
📝 **Automatic Tracking**: Updated all coordination files automatically
🔄 **Agent Coordination**: Signaled docker-expert for review
✅ **Zero Manual Work**: All orchestration handled by hooks

This shows how the hooks transform manual coordination into automatic, reliable workflows!
