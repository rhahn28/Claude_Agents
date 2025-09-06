#!/usr/bin/env python3
"""
Database-specific hooks for database-expert, mongodb-expert, postgres-expert, sql-expert
Validates database operations, SQL security, schema changes, and data integrity
"""

import json
import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def detect_sql_injection_risks(content: str, file_path: str) -> tuple[str, list]:
    """Detect SQL injection vulnerabilities"""
    
    vulnerabilities = []
    
    # High-risk SQL injection patterns
    high_risk_patterns = [
        (r"SELECT.*\+.*input\(", "SQL injection via string concatenation with user input"),
        (r"INSERT.*\+.*input\(", "SQL injection in INSERT statement"),
        (r"UPDATE.*\+.*input\(", "SQL injection in UPDATE statement"),
        (r"DELETE.*\+.*input\(", "SQL injection in DELETE statement"),
        (r"WHERE.*\+.*input\(", "SQL injection in WHERE clause"),
        (r"execute\s*\(\s*['\"].*\+", "SQL injection via execute() with concatenation"),
        (r"query\s*\(\s*['\"].*\+", "SQL injection via query() with concatenation"),
        (r"f['\"].*\{.*input\(.*\}.*['\"].*execute", "SQL injection via f-string with user input"),
        (r"%s.*format.*input\(", "SQL injection via string formatting"),
    ]
    
    # Medium-risk patterns
    medium_risk_patterns = [
        (r"ORDER BY.*\+", "Potential SQL injection in ORDER BY clause"),
        (r"LIMIT.*\+", "Potential SQL injection in LIMIT clause"),
        (r"raw\(\s*['\"].*\+", "Raw SQL with concatenation"),
        (r"\.sql\s*=.*\+", "SQL property assignment with concatenation"),
    ]
    
    for pattern, description in high_risk_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            vulnerabilities.append(f"🚨 HIGH RISK: {description}")
    
    for pattern, description in medium_risk_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            vulnerabilities.append(f"⚠️ MEDIUM RISK: {description}")
    
    # Check for parameterized queries (good practice)
    has_parameterized = bool(re.search(r"\?|%s|\$\d+|:[\w]+", content))
    if not has_parameterized and any(re.search(pat, content, re.IGNORECASE) for pat, _ in high_risk_patterns):
        vulnerabilities.append("💡 RECOMMENDATION: Use parameterized queries instead of string concatenation")
    
    if len([v for v in vulnerabilities if "HIGH RISK" in v]) >= 1:
        return "HIGH", vulnerabilities
    elif len([v for v in vulnerabilities if "MEDIUM RISK" in v]) >= 2:
        return "MEDIUM", vulnerabilities
    elif vulnerabilities:
        return "LOW", vulnerabilities
    
    return "NONE", []

def check_dangerous_database_operations(content: str, file_path: str) -> tuple[str, list]:
    """Check for dangerous database operations"""
    
    dangerous_ops = []
    
    # Schema-altering operations
    schema_patterns = [
        (r"DROP\s+TABLE", "DROP TABLE - permanent data loss risk"),
        (r"DROP\s+DATABASE", "DROP DATABASE - catastrophic data loss risk"),
        (r"TRUNCATE", "TRUNCATE - all data deletion risk"),
        (r"DELETE\s+FROM.*WHERE", "DELETE operation - verify WHERE clause"),
        (r"ALTER\s+TABLE.*DROP", "ALTER TABLE DROP - column/data loss risk"),
        (r"UPDATE.*WHERE", "UPDATE operation - verify WHERE clause scope"),
    ]
    
    # Privilege escalation
    privilege_patterns = [
        (r"GRANT\s+ALL", "GRANT ALL privileges - excessive permissions"),
        (r"GRANT.*SUPER", "SUPER privilege grant - administrative access"),
        (r"CREATE\s+USER.*IDENTIFIED\s+BY\s*['\"][^'\"]*['\"]", "Hardcoded password in user creation"),
        (r"ALTER\s+USER.*PASSWORD", "Password change operation"),
    ]
    
    # Mass operations
    mass_op_patterns = [
        (r"DELETE\s+FROM\s+\w+\s*;", "DELETE without WHERE - all records deletion"),
        (r"UPDATE\s+\w+\s+SET.*[^WHERE]", "UPDATE without WHERE - all records modification"),
        (r"INSERT.*SELECT.*FROM", "Mass INSERT operation"),
        (r"LOAD\s+DATA", "LOAD DATA operation - bulk import"),
    ]
    
    for pattern, description in schema_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            dangerous_ops.append(f"🗂️ SCHEMA: {description}")
    
    for pattern, description in privilege_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            dangerous_ops.append(f"🔑 PRIVILEGE: {description}")
    
    for pattern, description in mass_op_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            dangerous_ops.append(f"⚡ MASS OP: {description}")
    
    # Determine risk level based on operation types
    schema_ops = len([op for op in dangerous_ops if "SCHEMA:" in op])
    privilege_ops = len([op for op in dangerous_ops if "PRIVILEGE:" in op])
    mass_ops = len([op for op in dangerous_ops if "MASS OP:" in op])
    
    if schema_ops >= 1 or privilege_ops >= 1:
        return "HIGH", dangerous_ops
    elif mass_ops >= 2 or (mass_ops >= 1 and dangerous_ops):
        return "MEDIUM", dangerous_ops
    elif dangerous_ops:
        return "LOW", dangerous_ops
    
    return "NONE", []

def check_database_best_practices(content: str, file_path: str) -> list:
    """Check for database best practices"""
    
    recommendations = []
    
    # Connection management
    if ("connect(" in content or "Connection(" in content) and "close()" not in content:
        recommendations.append("🔌 Use connection pooling or ensure connections are properly closed")
    
    # Transaction management
    if any(op in content.upper() for op in ["INSERT", "UPDATE", "DELETE"]) and "BEGIN" not in content.upper():
        recommendations.append("💱 Consider using transactions for data consistency")
    
    # Index usage
    if "ORDER BY" in content.upper() and "INDEX" not in content.upper():
        recommendations.append("🔍 Consider adding indexes for ORDER BY performance")
    
    # Error handling
    if any(db_op in content for db_op in ["execute(", "query(", "commit("]) and "except" not in content.lower():
        recommendations.append("⚠️ Add error handling for database operations")
    
    # Backup considerations
    if any(dangerous in content.upper() for dangerous in ["DROP", "TRUNCATE", "DELETE FROM"]):
        recommendations.append("💾 Ensure database backups are current before destructive operations")
    
    # Performance considerations
    if "SELECT *" in content.upper():
        recommendations.append("📊 Avoid SELECT * - specify required columns for better performance")
    
    # Security practices
    if "password" in content.lower() and "hash" not in content.lower():
        recommendations.append("🔐 Ensure passwords are properly hashed before storage")
    
    return recommendations

def validate_database_schema_changes(content: str, file_path: str) -> tuple[str, list]:
    """Validate database schema changes"""
    
    schema_issues = []
    
    # Check for migration patterns
    migration_patterns = [
        (r"ADD\s+COLUMN.*NOT\s+NULL", "Adding NOT NULL column without default - may fail on existing data"),
        (r"ALTER.*COLUMN.*TYPE", "Column type change - potential data loss"),
        (r"DROP\s+COLUMN", "Column drop - permanent data loss"),
        (r"ADD.*UNIQUE", "Adding unique constraint - may fail if duplicates exist"),
        (r"ADD.*FOREIGN\s+KEY", "Adding foreign key - may fail if referential integrity violated"),
    ]
    
    for pattern, description in migration_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            schema_issues.append(f"📋 MIGRATION: {description}")
    
    # Check for data migration scripts
    if re.search(r"INSERT.*SELECT", content, re.IGNORECASE) and len(schema_issues) > 0:
        schema_issues.append("🔄 Data migration detected - verify data integrity after schema changes")
    
    if len(schema_issues) >= 3:
        return "HIGH", schema_issues
    elif len(schema_issues) >= 1:
        return "MEDIUM", schema_issues
    
    return "LOW", schema_issues

def main():
    try:
        input_data = HookUtils.read_json_input()
        project_dir = HookUtils.get_project_dir()
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only process file operations that might contain database code
        if tool_name not in ["Write", "Edit", "MultiEdit", "Task"]:
            sys.exit(0)
        
        file_path = tool_input.get("filePath", "")
        content = tool_input.get("content", "")
        
        # Skip if no content or not database-related
        if not content:
            sys.exit(0)
        
        # Check if content contains database operations
        db_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "execute(", "query(", "cursor", "connection"]
        if not any(keyword.lower() in content.lower() for keyword in db_keywords):
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Database security analysis
        injection_risk, injection_issues = detect_sql_injection_risks(content, file_path)
        dangerous_risk, dangerous_ops = check_dangerous_database_operations(content, file_path)
        schema_risk, schema_issues = validate_database_schema_changes(content, file_path)
        recommendations = check_database_best_practices(content, file_path)
        
        # Determine overall risk
        all_risks = [injection_risk, dangerous_risk, schema_risk]
        if "HIGH" in all_risks:
            overall_risk = "HIGH"
        elif "MEDIUM" in all_risks:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Block on SQL injection vulnerabilities
        if injection_risk == "HIGH":
            injection_details = "\n".join([f"• {issue}" for issue in injection_issues])
            HookUtils.block_with_error(f"🚫 SQL INJECTION RISK - OPERATION BLOCKED\n\n{injection_details}\n\nFile: {file_path}\n\nUse parameterized queries to prevent SQL injection attacks.")
        
        # Block on dangerous operations without confirmation
        if dangerous_risk == "HIGH":
            dangerous_details = "\n".join([f"• {op}" for op in dangerous_ops])
            HookUtils.block_with_error(f"🚫 DANGEROUS DATABASE OPERATION - CONFIRMATION REQUIRED\n\n{dangerous_details}\n\nFile: {file_path}\n\nThese operations can cause data loss. Please confirm with database administrator.")
        
        # Human confirmation for medium-high risk operations
        if overall_risk == "HIGH" or (overall_risk == "MEDIUM" and (dangerous_risk == "MEDIUM" or schema_risk == "MEDIUM")):
            all_issues = injection_issues + dangerous_ops + schema_issues
            issue_text = "\n".join([f"• {issue}" for issue in all_issues])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"🗄️ DATABASE OPERATION REVIEW\n\n{issue_text}\n\nFile: {file_path}\n\nPlease review these database operations carefully."
                }
            })
        
        # Success with recommendations
        success_msg = "✅ Database validation completed"
        
        if overall_risk == "MEDIUM" and dangerous_risk != "HIGH":
            medium_issues = []
            if injection_risk == "MEDIUM":
                medium_issues.extend(injection_issues[:2])
            if schema_risk == "MEDIUM":
                medium_issues.extend(schema_issues[:1])
            
            if medium_issues:
                warning_text = "\n".join([f"⚠️ {issue}" for issue in medium_issues])
                success_msg += f"\n\nDatabase Warnings:\n{warning_text}"
        
        if recommendations and overall_risk == "LOW":
            rec_text = "\n".join([f"💡 {rec}" for rec in recommendations[:3]])
            success_msg += f"\n\nRecommendations:\n{rec_text}"
        
        HookUtils.allow_with_message(success_msg, suppress=(overall_risk == "LOW" and not recommendations))
        
    except Exception as e:
        print(f"Database hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
