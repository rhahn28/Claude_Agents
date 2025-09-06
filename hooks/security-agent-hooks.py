#!/usr/bin/env python3
"""
Security-specific hooks for security-auditor, compliance-officer
Validates security practices, compliance requirements, and vulnerability detection
"""

import json
import sys
import os
import re
import hashlib
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def detect_secrets_and_credentials(content: str, file_path: str) -> tuple[str, list]:
    """Detect potential secrets and credentials in code"""
    
    secrets_found = []
    
    # High-confidence secret patterns
    high_confidence_patterns = [
        (r"-----BEGIN [A-Z ]+-----", "Private key detected"),
        (r"['\"]?[A-Za-z0-9]{32,}['\"]?\s*[:=]\s*['\"][A-Za-z0-9+/]{20,}={0,2}['\"]", "Base64 encoded secret"),
        (r"sk_live_[A-Za-z0-9]{24,}", "Stripe live secret key"),
        (r"sk_test_[A-Za-z0-9]{24,}", "Stripe test secret key"),
        (r"pk_live_[A-Za-z0-9]{24,}", "Stripe live publishable key"),
        (r"AKIA[0-9A-Z]{16}", "AWS access key ID"),
        (r"['\"]?[A-Za-z0-9/+]{40}['\"]?", "AWS secret access key pattern"),
        (r"ghp_[A-Za-z0-9]{36}", "GitHub personal access token"),
        (r"ghs_[A-Za-z0-9]{36}", "GitHub app token"),
    ]
    
    # Medium-confidence patterns
    medium_confidence_patterns = [
        (r"password\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded password"),
        (r"api[_-]?key\s*[:=]\s*['\"][^'\"]{10,}['\"]", "API key"),
        (r"secret[_-]?key\s*[:=]\s*['\"][^'\"]{10,}['\"]", "Secret key"),
        (r"auth[_-]?token\s*[:=]\s*['\"][^'\"]{20,}['\"]", "Authentication token"),
        (r"access[_-]?token\s*[:=]\s*['\"][^'\"]{20,}['\"]", "Access token"),
        (r"private[_-]?key\s*[:=]\s*['\"][^'\"]{20,}['\"]", "Private key"),
        (r"database[_-]?url\s*[:=]\s*['\"].*://.*:.*@.*['\"]", "Database connection string with credentials"),
    ]
    
    # Check high confidence patterns
    for pattern, description in high_confidence_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            secrets_found.append(f"🔒 HIGH CONFIDENCE: {description}")
    
    # Check medium confidence patterns
    for pattern, description in medium_confidence_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # Exclude common test/example values
            matched_text = match.group(0).lower()
            if not any(test_val in matched_text for test_val in ["test", "example", "demo", "placeholder", "xxx"]):
                secrets_found.append(f"⚠️ MEDIUM CONFIDENCE: {description}")
    
    if len([s for s in secrets_found if "HIGH CONFIDENCE" in s]) >= 1:
        return "HIGH", secrets_found
    elif len(secrets_found) >= 2:
        return "MEDIUM", secrets_found
    elif secrets_found:
        return "LOW", secrets_found
    
    return "NONE", []

def check_security_vulnerabilities(content: str, file_path: str) -> tuple[str, list]:
    """Check for common security vulnerabilities"""
    
    vulnerabilities = []
    
    # Code injection vulnerabilities
    injection_patterns = [
        (r"eval\s*\(.*\+", "Code injection via eval with concatenation"),
        (r"exec\s*\(.*\+", "Code injection via exec with concatenation"),
        (r"__import__\s*\(.*input\(", "Dynamic import with user input"),
        (r"subprocess\.[a-zA-Z]*\(.*shell=True.*\+", "Command injection via subprocess"),
        (r"os\.system\s*\(.*\+", "Command injection via os.system"),
        (r"sql.*\+.*input\(", "SQL injection pattern"),
        (r"\.format\s*\(.*input\(", "Format string vulnerability"),
    ]
    
    # XSS and web vulnerabilities
    web_patterns = [
        (r"innerHTML\s*=.*\+", "XSS via innerHTML"),
        (r"document\.write\s*\(.*\+", "XSS via document.write"),
        (r"dangerouslySetInnerHTML.*\+", "XSS via dangerouslySetInnerHTML"),
        (r"window\.location\s*=.*\+", "Open redirect vulnerability"),
        (r"postMessage\s*\(.*,\s*\*", "PostMessage to any origin - security risk"),
    ]
    
    # Crypto vulnerabilities
    crypto_patterns = [
        (r"md5\s*\(", "MD5 usage - cryptographically broken"),
        (r"sha1\s*\(", "SHA1 usage - cryptographically weak"),
        (r"DES|3DES", "DES encryption - weak algorithm"),
        (r"RC4", "RC4 encryption - broken algorithm"),
        (r"random\.random\(\)", "Weak random number generator for security"),
    ]
    
    all_patterns = injection_patterns + web_patterns + crypto_patterns
    
    for pattern, description in all_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            vulnerabilities.append(f"🚨 VULNERABILITY: {description}")
    
    # Determine risk level
    if len(vulnerabilities) >= 3:
        return "HIGH", vulnerabilities
    elif len(vulnerabilities) >= 1:
        return "MEDIUM", vulnerabilities
    
    return "LOW", vulnerabilities

def check_compliance_requirements(content: str, file_path: str) -> tuple[str, list]:
    """Check for compliance-related issues (GDPR, HIPAA, etc.)"""
    
    compliance_issues = []
    
    # Data privacy patterns
    privacy_patterns = [
        (r"personal[_-]?data", "Personal data handling detected - ensure GDPR compliance"),
        (r"pii|personally[_-]?identifiable", "PII detected - privacy review required"),
        (r"medical|health[_-]?record", "Health data detected - HIPAA compliance required"),
        (r"credit[_-]?card|payment[_-]?info", "Payment data detected - PCI DSS compliance required"),
        (r"ssn|social[_-]?security", "SSN detected - sensitive data handling required"),
        (r"cookie.*tracking", "Tracking cookies - privacy policy required"),
    ]
    
    # Logging and audit patterns
    audit_patterns = [
        (r"log.*password|log.*secret", "Sensitive data in logs - compliance violation"),
        (r"print.*password|print.*token", "Sensitive data in output - security risk"),
        (r"console\.log.*password", "Password in console logs - security risk"),
    ]
    
    for pattern, description in privacy_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            compliance_issues.append(f"⚖️ COMPLIANCE: {description}")
    
    for pattern, description in audit_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            compliance_issues.append(f"📋 AUDIT: {description}")
    
    if len(compliance_issues) >= 2:
        return "HIGH", compliance_issues
    elif compliance_issues:
        return "MEDIUM", compliance_issues
    
    return "LOW", compliance_issues

def check_secure_coding_practices(content: str, file_path: str) -> list:
    """Check for secure coding best practices"""
    
    recommendations = []
    
    # Input validation
    if "input(" in content and "validate" not in content.lower():
        recommendations.append("📝 Add input validation for user inputs")
    
    # Error handling
    if "except:" in content:
        recommendations.append("🔍 Use specific exception handling instead of bare except")
    
    # File operations
    if ("open(" in content or "file(" in content) and "with " not in content:
        recommendations.append("📁 Use context managers (with statement) for file operations")
    
    # Crypto recommendations
    if any(weak in content.lower() for weak in ["md5", "sha1"]) and "hashlib" in content:
        recommendations.append("🔐 Use SHA-256 or stronger hashing algorithms")
    
    return recommendations

def main():
    try:
        input_data = HookUtils.read_json_input()
        project_dir = HookUtils.get_project_dir()
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Process all file operations for security scanning
        if tool_name not in ["Write", "Edit", "MultiEdit", "Task"]:
            sys.exit(0)
        
        file_path = tool_input.get("filePath", "")
        content = tool_input.get("content", "")
        
        # Skip binary files and very large files
        if not content or len(content) > 100000:
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Security analysis
        secrets_risk, secrets_found = detect_secrets_and_credentials(content, file_path)
        vuln_risk, vulnerabilities = check_security_vulnerabilities(content, file_path)
        compliance_risk, compliance_issues = check_compliance_requirements(content, file_path)
        recommendations = check_secure_coding_practices(content, file_path)
        
        # Determine overall security risk
        all_risks = [secrets_risk, vuln_risk, compliance_risk]
        if "HIGH" in all_risks:
            overall_risk = "HIGH"
        elif "MEDIUM" in all_risks:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Block if secrets detected
        if secrets_risk == "HIGH":
            secret_details = "\n".join([f"• {secret}" for secret in secrets_found])
            HookUtils.block_with_error(f"🚫 SECRETS DETECTED - OPERATION BLOCKED\n\n{secret_details}\n\nFile: {file_path}\n\nRemove all secrets and credentials before proceeding. Use environment variables or secure vaults instead.")
        
        # Human confirmation for high security risk
        if overall_risk == "HIGH":
            all_issues = secrets_found + vulnerabilities + compliance_issues
            issue_text = "\n".join([f"• {issue}" for issue in all_issues])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"🚨 SECURITY REVIEW REQUIRED\n\n{issue_text}\n\nFile: {file_path}\n\nThis code has security implications. Please review with security team."
                }
            })
        
        # Success with security recommendations
        success_msg = "✅ Security scan completed"
        
        if overall_risk == "MEDIUM":
            medium_issues = []
            if secrets_risk == "MEDIUM":
                medium_issues.extend(secrets_found[:2])
            if vuln_risk == "MEDIUM":
                medium_issues.extend(vulnerabilities[:2])
            if compliance_risk == "MEDIUM":
                medium_issues.extend(compliance_issues[:1])
            
            if medium_issues:
                warning_text = "\n".join([f"⚠️ {issue}" for issue in medium_issues])
                success_msg += f"\n\nSecurity Warnings:\n{warning_text}"
        
        if recommendations and overall_risk == "LOW":
            rec_text = "\n".join([f"💡 {rec}" for rec in recommendations[:2]])
            success_msg += f"\n\nRecommendations:\n{rec_text}"
        
        HookUtils.allow_with_message(success_msg, suppress=(overall_risk == "LOW" and not recommendations))
        
    except Exception as e:
        print(f"Security hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
