#!/usr/bin/env python3
"""
Business-specific hooks for business-analyst, requirements-analyst, api-designer, product-manager
Validates business logic, requirements compliance, API design, and product specifications
"""

import json
import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def validate_api_design_standards(content: str, file_path: str) -> tuple[str, list]:
    """Validate API design against REST and GraphQL best practices"""
    
    api_issues = []
    
    # REST API patterns
    rest_patterns = [
        (r"@app\.route\(['\"].*[A-Z].*['\"]", "REST: Avoid uppercase in URL paths"),
        (r"@app\.route\(['\"].*/\{[^}]+\}\{[^}]+\}['\"]", "REST: Avoid consecutive path parameters"),
        (r"/api/v\d+/.*get.*", "REST: Avoid verbs in URL paths (GET is implicit)"),
        (r"/api/v\d+/.*post.*", "REST: Avoid verbs in URL paths (POST is implicit)"),
        (r"@app\.route.*methods=.*GET.*POST", "REST: Single endpoint should not handle both GET and POST"),
    ]
    
    # GraphQL patterns
    graphql_patterns = [
        (r"type.*\{[^}]*String[^!][^}]*\}", "GraphQL: Consider making required fields non-nullable (!)"),
        (r"query.*\{[^}]*\{[^}]*\{[^}]*\{", "GraphQL: Query nesting too deep (>3 levels)"),
        (r"mutation.*[A-Z][a-z]", "GraphQL: Mutations should use camelCase"),
    ]
    
    # HTTP status code patterns
    status_code_patterns = [
        (r"return.*200.*error", "HTTP: Don't return 200 for error conditions"),
        (r"return.*404.*created", "HTTP: Don't return 404 for successful creation"),
        (r"return.*500.*validation", "HTTP: Use 400 for validation errors, not 500"),
    ]
    
    for pattern, description in rest_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            api_issues.append(f"🌐 REST: {description}")
    
    for pattern, description in graphql_patterns:
        if re.search(pattern, content):
            api_issues.append(f"📊 GraphQL: {description}")
    
    for pattern, description in status_code_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            api_issues.append(f"📟 HTTP: {description}")
    
    if len(api_issues) >= 3:
        return "MEDIUM", api_issues
    elif api_issues:
        return "LOW", api_issues
    
    return "NONE", []

def check_business_logic_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for business logic implementation patterns"""
    
    business_issues = []
    
    # Business rule validation
    validation_patterns = [
        (r"if.*age.*<.*0", "Business: Age cannot be negative - add validation"),
        (r"if.*price.*<.*0", "Business: Price cannot be negative - add validation"),
        (r"if.*quantity.*<.*0", "Business: Quantity cannot be negative - add validation"),
        (r"email.*@.*\..*", "Business: Email validation should use proper regex or library"),
        (r"phone.*\d{10}", "Business: Phone validation too simplistic - consider international formats"),
    ]
    
    # Domain-driven design patterns
    ddd_patterns = [
        (r"class.*Service.*\{", "DDD: Services should focus on domain logic, not data access"),
        (r"def.*calculate.*total.*\(.*\).*:", "DDD: Business calculations should be in domain entities"),
        (r"class.*Repository.*save.*business", "DDD: Repositories should not contain business logic"),
    ]
    
    # Error handling in business logic
    error_patterns = [
        (r"try:.*business.*except.*pass", "Business: Empty exception handling can hide business rule violations"),
        (r"if.*business.*:.*raise.*Exception\(", "Business: Use specific business exceptions instead of generic Exception"),
    ]
    
    for pattern, description in validation_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            business_issues.append(f"✅ VALIDATION: {description}")
    
    for pattern, description in ddd_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            business_issues.append(f"🏗️ ARCHITECTURE: {description}")
    
    for pattern, description in error_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            business_issues.append(f"⚠️ ERROR HANDLING: {description}")
    
    if len(business_issues) >= 3:
        return "MEDIUM", business_issues
    elif business_issues:
        return "LOW", business_issues
    
    return "NONE", []

def validate_requirements_coverage(content: str, file_path: str) -> tuple[str, list]:
    """Check if code implements documented requirements"""
    
    requirements_issues = []
    
    # Look for requirement keywords
    req_keywords = ["requirement", "spec", "must", "shall", "should", "todo", "fixme"]
    
    # Check for implemented requirements
    if any(keyword in content.lower() for keyword in req_keywords):
        # Check for TODO/FIXME without implementation
        todo_pattern = r"(TODO|FIXME|XXX):(.*)"
        todos = re.findall(todo_pattern, content, re.IGNORECASE)
        for todo_type, todo_text in todos:
            requirements_issues.append(f"📋 {todo_type.upper()}: {todo_text.strip()}")
        
        # Check for requirement traceability
        req_id_pattern = r"REQ[-_](\d+|[A-Z]+\d*)"
        req_ids = re.findall(req_id_pattern, content, re.IGNORECASE)
        if not req_ids and len(todos) > 0:
            requirements_issues.append("🔗 TRACEABILITY: Add requirement IDs for traceability")
    
    # Check for incomplete implementations
    incomplete_patterns = [
        (r"NotImplementedError", "Implementation incomplete - NotImplementedError found"),
        (r"pass\s*#.*implement", "Implementation incomplete - placeholder found"),
        (r"raise.*NotImplemented", "Implementation incomplete - NotImplementedError raised"),
    ]
    
    for pattern, description in incomplete_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            requirements_issues.append(f"⚠️ INCOMPLETE: {description}")
    
    if len([issue for issue in requirements_issues if "INCOMPLETE" in issue]) >= 1:
        return "HIGH", requirements_issues
    elif len(requirements_issues) >= 2:
        return "MEDIUM", requirements_issues
    elif requirements_issues:
        return "LOW", requirements_issues
    
    return "NONE", []

def check_product_compliance(content: str, file_path: str) -> tuple[str, list]:
    """Check for product management and compliance considerations"""
    
    compliance_issues = []
    
    # Feature flag patterns
    feature_patterns = [
        (r"if.*feature[_-]?flag", "FEATURE: Feature flag detected - ensure proper rollout strategy"),
        (r"experiment.*enabled", "A/B TEST: Experiment code detected - ensure proper metrics tracking"),
        (r"beta[_-]?feature", "BETA: Beta feature detected - ensure feedback collection"),
    ]
    
    # User experience patterns  
    ux_patterns = [
        (r"loading.*true.*false.*true", "UX: Loading state flickering - improve user experience"),
        (r"error.*message.*generic", "UX: Generic error messages - provide specific user guidance"),
        (r"timeout.*30\d\d\d", "UX: Long timeout (>30s) - consider user experience impact"),
    ]
    
    # Analytics and metrics
    analytics_patterns = [
        (r"track[_-]?event", "ANALYTICS: Event tracking found - ensure privacy compliance"),
        (r"user[_-]?id.*log", "PRIVACY: User ID in logs - review data privacy requirements"),
        (r"metrics.*user", "METRICS: User metrics collection - ensure consent obtained"),
    ]
    
    for pattern, description in feature_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            compliance_issues.append(f"🚩 {description}")
    
    for pattern, description in ux_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            compliance_issues.append(f"👥 {description}")
    
    for pattern, description in analytics_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            compliance_issues.append(f"📊 {description}")
    
    if len(compliance_issues) >= 2:
        return "MEDIUM", compliance_issues
    elif compliance_issues:
        return "LOW", compliance_issues
    
    return "NONE", []

def get_business_recommendations(content: str, file_path: str) -> list:
    """Get business-focused recommendations"""
    
    recommendations = []
    
    # Documentation recommendations
    if len(content) > 500 and not re.search(r'""".*"""', content, re.DOTALL):
        recommendations.append("📚 Add comprehensive docstrings for business logic")
    
    # Testing recommendations
    if any(biz_word in content.lower() for biz_word in ["calculate", "validate", "process", "business"]):
        if "test" not in content.lower():
            recommendations.append("🧪 Add unit tests for business logic validation")
    
    # Performance recommendations
    if "for.*in.*:" in content and "len(" in content:
        recommendations.append("⚡ Consider performance implications of loops in business calculations")
    
    # Monitoring recommendations
    if any(critical in content.lower() for critical in ["payment", "order", "transaction"]):
        recommendations.append("📊 Add monitoring and alerting for critical business operations")
    
    # Configuration recommendations
    if re.search(r'\d+\.\d+', content) and "config" not in content.lower():
        recommendations.append("⚙️ Extract business constants to configuration files")
    
    return recommendations

def main():
    try:
        input_data = HookUtils.read_json_input()
        project_dir = HookUtils.get_project_dir()
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only process file operations
        if tool_name not in ["Write", "Edit", "MultiEdit", "Task"]:
            sys.exit(0)
        
        file_path = tool_input.get("filePath", "")
        content = tool_input.get("content", "")
        
        # Skip if no content
        if not content:
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Business validation analysis
        api_risk, api_issues = validate_api_design_standards(content, file_path)
        business_risk, business_issues = check_business_logic_patterns(content, file_path)
        req_risk, req_issues = validate_requirements_coverage(content, file_path)
        compliance_risk, compliance_issues = check_product_compliance(content, file_path)
        recommendations = get_business_recommendations(content, file_path)
        
        # Determine overall risk
        all_risks = [api_risk, business_risk, req_risk, compliance_risk]
        if "HIGH" in all_risks:
            overall_risk = "HIGH"
        elif "MEDIUM" in all_risks:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Block on incomplete implementations in production code
        if req_risk == "HIGH" and not any(test_path in file_path.lower() for test_path in ["test", "spec", "demo"]):
            incomplete_details = "\n".join([f"• {issue}" for issue in req_issues if "INCOMPLETE" in issue])
            HookUtils.block_with_error(f"🚫 INCOMPLETE IMPLEMENTATION - PRODUCTION BLOCK\n\n{incomplete_details}\n\nFile: {file_path}\n\nComplete implementation before deploying to production.")
        
        # Human confirmation for medium-high business risk
        if overall_risk == "MEDIUM":
            all_issues = api_issues + business_issues + req_issues + compliance_issues
            issue_text = "\n".join([f"• {issue}" for issue in all_issues])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"💼 BUSINESS LOGIC REVIEW\n\n{issue_text}\n\nFile: {file_path}\n\nPlease review these business implementation concerns."
                }
            })
        
        # Success with business insights
        success_msg = "✅ Business validation completed"
        
        if overall_risk == "LOW" and any([api_issues, business_issues, compliance_issues]):
            insights = []
            insights.extend([f"💡 {issue}" for issue in api_issues[:1]])
            insights.extend([f"💡 {issue}" for issue in business_issues[:1]])
            insights.extend([f"💡 {issue}" for issue in compliance_issues[:1]])
            
            if insights:
                insight_text = "\n".join(insights)
                success_msg += f"\n\nBusiness Insights:\n{insight_text}"
        
        if recommendations and overall_risk == "LOW":
            rec_text = "\n".join([f"📋 {rec}" for rec in recommendations[:2]])
            success_msg += f"\n\nRecommendations:\n{rec_text}"
        
        HookUtils.allow_with_message(success_msg, suppress=(overall_risk == "LOW" and not recommendations and not any([api_issues, business_issues, compliance_issues])))
        
    except Exception as e:
        print(f"Business hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
