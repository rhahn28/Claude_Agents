#!/usr/bin/env python3
"""
Docker/DevOps-specific hooks for docker-expert, devops-engineer, kubernetes-expert, terraform-expert
Validates containerization, infrastructure as code, and deployment configurations
"""

import json
import sys
import os
import re
import yaml
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def validate_docker_configuration(project_dir: str, tool_input: dict) -> tuple[bool, str, str]:
    """Validate Docker configuration files"""
    
    file_path = tool_input.get("filePath", "")
    content = tool_input.get("content", "")
    
    if "dockerfile" not in file_path.lower() and "docker-compose" not in file_path.lower():
        return True, "LOW", "Not a Docker configuration file"
    
    issues = []
    risk_level = "LOW"
    
    if "dockerfile" in file_path.lower():
        # Dockerfile validation
        dockerfile_issues = [
            (r"FROM.*:latest", "Using :latest tag - specify explicit versions"),
            (r"RUN.*apt-get update.*&&.*apt-get install", "apt-get without cleanup - increases image size"),
            (r"ADD\s+http", "Using ADD for URLs - prefer RUN with wget/curl"),
            (r"USER\s+root", "Running as root user - security risk"),
            (r"COPY\s+\.\s+", "Copying entire context - use .dockerignore"),
        ]
        
        for pattern, issue in dockerfile_issues:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"🐳 DOCKERFILE: {issue}")
                risk_level = "MEDIUM"
    
    elif "docker-compose" in file_path.lower():
        # Docker Compose validation
        compose_issues = []
        
        try:
            # Basic YAML parsing check
            if content:
                yaml.safe_load(content)
        except yaml.YAMLError:
            issues.append("🐳 COMPOSE: Invalid YAML syntax")
            risk_level = "HIGH"
        
        compose_patterns = [
            (r"image:.*:latest", "Using :latest tag in compose - specify versions"),
            (r"privileged:\s*true", "privileged mode enabled - security risk"),
            (r"network_mode:\s*host", "host network mode - security concern"),
            (r"volumes:.*:/var/run/docker.sock", "Mounting docker socket - high security risk"),
        ]
        
        for pattern, issue in compose_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"🐳 COMPOSE: {issue}")
                risk_level = "HIGH" if "security risk" in issue else "MEDIUM"
    
    if issues:
        return False, risk_level, "; ".join(issues)
    
    return True, "LOW", "Docker configuration validated"

def validate_kubernetes_configuration(tool_input: dict) -> tuple[bool, str, str]:
    """Validate Kubernetes manifests"""
    
    file_path = tool_input.get("filePath", "")
    content = tool_input.get("content", "")
    
    k8s_extensions = [".yaml", ".yml"]
    if not any(ext in file_path for ext in k8s_extensions):
        return True, "LOW", "Not a Kubernetes manifest"
    
    # Check if it's actually a K8s manifest
    k8s_keywords = ["apiVersion", "kind", "metadata", "spec"]
    if not all(keyword in content for keyword in k8s_keywords[:2]):
        return True, "LOW", "Not a Kubernetes manifest"
    
    issues = []
    risk_level = "LOW"
    
    k8s_security_issues = [
        (r"runAsUser:\s*0", "Running as root user (UID 0) - security risk"),
        (r"privileged:\s*true", "Privileged container - high security risk"),
        (r"hostNetwork:\s*true", "Host network access - security risk"),
        (r"hostPID:\s*true", "Host PID namespace - security risk"),
        (r"allowPrivilegeEscalation:\s*true", "Privilege escalation allowed - security risk"),
    ]
    
    k8s_best_practices = [
        (r"resources:", "Resource limits/requests not defined"),
        (r"livenessProbe:", "Liveness probe not configured"),
        (r"readinessProbe:", "Readiness probe not configured"),
    ]
    
    for pattern, issue in k8s_security_issues:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"☸️ K8S SECURITY: {issue}")
            risk_level = "HIGH"
    
    # Check for missing best practices (inverse logic)
    for pattern, issue in k8s_best_practices:
        if not re.search(pattern, content, re.IGNORECASE) and "kind: Deployment" in content:
            issues.append(f"☸️ K8S BEST PRACTICE: {issue}")
            if risk_level == "LOW":
                risk_level = "MEDIUM"
    
    if issues:
        return False, risk_level, "; ".join(issues)
    
    return True, "LOW", "Kubernetes configuration validated"

def validate_terraform_configuration(tool_input: dict) -> tuple[bool, str, str]:
    """Validate Terraform configurations"""
    
    file_path = tool_input.get("filePath", "")
    content = tool_input.get("content", "")
    
    if not file_path.endswith(".tf"):
        return True, "LOW", "Not a Terraform file"
    
    issues = []
    risk_level = "LOW"
    
    terraform_security_issues = [
        (r'default\s*=\s*".*password.*"', "Hardcoded password in Terraform"),
        (r'default\s*=\s*".*secret.*"', "Hardcoded secret in Terraform"),
        (r'default\s*=\s*".*key.*"', "Hardcoded key in Terraform"),
        (r"public_access_block.*=.*false", "S3 public access not blocked"),
        (r"acl.*=.*public-read", "Public read ACL - security risk"),
    ]
    
    terraform_best_practices = [
        (r"terraform\s*{", "Terraform version constraint not specified"),
        (r"backend\s*\"", "Remote backend configuration missing"),
        (r"tags\s*=", "Resource tagging not implemented"),
    ]
    
    for pattern, issue in terraform_security_issues:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"🏗️ TERRAFORM SECURITY: {issue}")
            risk_level = "HIGH"
    
    # Check for missing best practices
    if "resource " in content:
        for pattern, issue in terraform_best_practices:
            if not re.search(pattern, content, re.IGNORECASE):
                issues.append(f"🏗️ TERRAFORM BEST PRACTICE: {issue}")
                if risk_level == "LOW":
                    risk_level = "MEDIUM"
    
    if issues:
        return False, risk_level, "; ".join(issues)
    
    return True, "LOW", "Terraform configuration validated"

def check_infrastructure_dependencies(project_dir: str, tool_input: dict) -> tuple[bool, str]:
    """Check for infrastructure dependencies and coordination"""
    
    file_path = tool_input.get("filePath", "")
    
    # If creating infrastructure files, ensure proper coordination
    infra_files = ["docker-compose.yml", "Dockerfile", "terraform", "kubernetes", ".tf", ".yaml"]
    is_infra_file = any(pattern in file_path.lower() for pattern in infra_files)
    
    if is_infra_file:
        # Check if other infrastructure files exist that might conflict
        existing_docker = HookUtils.file_exists(project_dir, "docker-compose.yml")
        existing_k8s = any(HookUtils.file_exists(project_dir, f) for f in ["deployment.yaml", "service.yaml"])
        
        if existing_docker and "kubernetes" in file_path.lower():
            return False, "🔄 INFRASTRUCTURE CONFLICT: Both Docker Compose and Kubernetes configurations present. Choose one orchestration method."
        
        if existing_k8s and "docker-compose" in file_path.lower():
            return False, "🔄 INFRASTRUCTURE CONFLICT: Kubernetes manifests exist. Adding Docker Compose may cause conflicts."
    
    return True, "Infrastructure dependencies validated"

def main():
    try:
        input_data = HookUtils.read_json_input()
        project_dir = HookUtils.get_project_dir()
        
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        
        # Only process infrastructure-related tools
        if tool_name not in ["Write", "Edit", "MultiEdit", "Task"]:
            sys.exit(0)
        
        # Check if this is infrastructure-related
        file_path = tool_input.get("filePath", "")
        infra_keywords = ["docker", "kubernetes", "terraform", ".tf", ".yaml", ".yml", "compose"]
        if not any(keyword in file_path.lower() for keyword in infra_keywords):
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Validate configurations
        all_issues = []
        highest_risk = "LOW"
        
        # Docker validation
        docker_valid, docker_risk, docker_msg = validate_docker_configuration(project_dir, tool_input)
        if not docker_valid:
            all_issues.append(docker_msg)
            if docker_risk == "HIGH":
                highest_risk = "HIGH"
            elif docker_risk == "MEDIUM" and highest_risk == "LOW":
                highest_risk = "MEDIUM"
        
        # Kubernetes validation
        k8s_valid, k8s_risk, k8s_msg = validate_kubernetes_configuration(tool_input)
        if not k8s_valid:
            all_issues.append(k8s_msg)
            if k8s_risk == "HIGH":
                highest_risk = "HIGH"
            elif k8s_risk == "MEDIUM" and highest_risk == "LOW":
                highest_risk = "MEDIUM"
        
        # Terraform validation
        tf_valid, tf_risk, tf_msg = validate_terraform_configuration(tool_input)
        if not tf_valid:
            all_issues.append(tf_msg)
            if tf_risk == "HIGH":
                highest_risk = "HIGH"
            elif tf_risk == "MEDIUM" and highest_risk == "LOW":
                highest_risk = "MEDIUM"
        
        # Infrastructure dependencies
        deps_valid, deps_msg = check_infrastructure_dependencies(project_dir, tool_input)
        if not deps_valid:
            HookUtils.block_with_error(deps_msg)
        
        # Human confirmation for high-risk configurations
        if highest_risk == "HIGH":
            issue_text = "\n".join([f"• {issue}" for issue in all_issues])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"🚨 INFRASTRUCTURE SECURITY REVIEW REQUIRED\n\n{issue_text}\n\nFile: {file_path}\n\nThese configurations have security implications. Please review carefully."
                }
            })
        
        # Block for medium risk with multiple issues
        if highest_risk == "MEDIUM" and len(all_issues) >= 3:
            issue_text = "\n".join([f"• {issue}" for issue in all_issues])
            HookUtils.block_with_error(f"🛑 INFRASTRUCTURE ISSUES DETECTED:\n\n{issue_text}\n\nPlease address these issues before proceeding.")
        
        # Success with warnings
        success_msg = f"✅ Infrastructure validation passed\n{deps_msg}"
        if highest_risk == "MEDIUM" and all_issues:
            warning_text = "\n".join([f"⚠️ {issue}" for issue in all_issues[:2]])
            success_msg += f"\n\nWarnings:\n{warning_text}"
        
        HookUtils.allow_with_message(success_msg, suppress=highest_risk == "LOW")
        
    except Exception as e:
        print(f"Infrastructure hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
