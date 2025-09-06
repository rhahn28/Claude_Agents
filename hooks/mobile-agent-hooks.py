#!/usr/bin/env python3
"""
Mobile development hooks for swift-expert, kotlin-expert, react-native-expert, flutter-expert
Validates mobile app development, performance, and platform-specific best practices
"""

import json
import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def check_mobile_performance_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for mobile performance anti-patterns"""
    
    performance_issues = []
    
    # iOS/Swift patterns
    ios_patterns = [
        (r'UIImageView.*image.*UIImage\(named:', "iOS: Loading images on main thread - consider background loading"),
        (r'viewDidLoad.*for.*in.*array', "iOS: Heavy computation in viewDidLoad - move to background"),
        (r'tableView.*cellForRowAt.*UIImage\(data:', "iOS: Image processing in table cells - causes scrolling lag"),
        (r'@objc.*func.*while.*true', "iOS: Infinite loops in main thread - will freeze UI"),
        (r'URLSession.*dataTask.*DispatchQueue\.main', "iOS: Network on main thread - use background queues"),
    ]
    
    # Android/Kotlin patterns
    android_patterns = [
        (r'onCreate.*for.*in.*large', "Android: Heavy work in onCreate - move to AsyncTask or coroutines"),
        (r'getView.*findViewById', "Android: findViewById in getView - use ViewHolder pattern"),
        (r'onDraw.*Canvas.*for.*in', "Android: Complex drawing in onDraw - pre-compute or cache"),
        (r'SharedPreferences.*edit\(\).*apply\(\).*for', "Android: Multiple SharedPreferences writes - batch operations"),
        (r'Thread\(\s*\{.*UI.*\}\s*\)\.start', "Android: Direct UI updates from background threads"),
    ]
    
    # React Native patterns
    rn_patterns = [
        (r'FlatList.*data.*\.map\(', "RN: Avoid map() with FlatList - use data prop directly"),
        (r'ScrollView.*\.map\(.*\>.*100', "RN: Large ScrollView lists - use FlatList for performance"),
        (r'Image.*source.*require\(.*\.map', "RN: Dynamic require() in loops - preload images"),
        (r'Animated\.timing.*loop.*while', "RN: Infinite animations without cleanup - memory leaks"),
        (r'console\.log.*render\(\)', "RN: Console logs in render - impacts performance"),
    ]
    
    # Flutter patterns
    flutter_patterns = [
        (r'build.*for.*in.*large', "Flutter: Heavy computation in build method - use builders"),
        (r'StatefulWidget.*setState.*for.*in', "Flutter: Multiple setState calls - batch updates"),
        (r'Image\.asset.*ListView\.builder', "Flutter: Loading images in ListView - use caching"),
        (r'FutureBuilder.*ListView\.builder', "Flutter: Nested async builders - performance issues"),
    ]
    
    all_patterns = ios_patterns + android_patterns + rn_patterns + flutter_patterns
    
    for pattern, description in all_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            performance_issues.append(f"⚡ {description}")
    
    if len(performance_issues) >= 3:
        return "HIGH", performance_issues
    elif len(performance_issues) >= 1:
        return "MEDIUM", performance_issues
    
    return "NONE", []

def check_mobile_security_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for mobile security vulnerabilities"""
    
    security_issues = []
    
    # iOS Security patterns
    ios_security = [
        (r'NSUserDefaults.*password|UserDefaults.*password', "iOS: Password in UserDefaults - use Keychain"),
        (r'NSLog.*password|print.*password', "iOS: Password in logs - security risk"),
        (r'allowsArbitraryLoads.*true', "iOS: ATS disabled - security vulnerability"),
        (r'NSURLRequest.*HTTPMethod.*POST.*password', "iOS: Password in HTTP request - use HTTPS"),
        (r'kSecAttrAccessibleAlways', "iOS: Keychain always accessible - reduce accessibility"),
    ]
    
    # Android Security patterns
    android_security = [
        (r'SharedPreferences.*password', "Android: Password in SharedPreferences - use KeyStore"),
        (r'Log\.[devi].*password|println.*password', "Android: Password in logs - security risk"),
        (r'HTTP://|http://', "Android: HTTP usage - migrate to HTTPS"),
        (r'WebView.*setJavaScriptEnabled\(true\)', "Android: JavaScript enabled without validation - XSS risk"),
        (r'Intent.*FLAG_ACTIVITY_NEW_TASK.*data', "Android: Intent with sensitive data - validate recipient"),
    ]
    
    # React Native Security
    rn_security = [
        (r'AsyncStorage.*password|SecureStore.*password', "RN: Password storage - ensure proper encryption"),
        (r'fetch\([\'"]http://|axios.*http://', "RN: HTTP requests - use HTTPS only"),
        (r'WebView.*source.*uri.*http://', "RN: HTTP in WebView - security risk"),
        (r'__DEV__.*false.*console\.log.*token', "RN: Tokens in production logs - remove debug code"),
    ]
    
    # Flutter Security
    flutter_security = [
        (r'SharedPreferences.*password', "Flutter: Password in SharedPreferences - use flutter_secure_storage"),
        (r'http\.get\(|http\.post\(', "Flutter: HTTP package usage - migrate to HTTPS"),
        (r'WebView.*initialUrl.*http://', "Flutter: HTTP in WebView - security vulnerability"),
    ]
    
    all_security = ios_security + android_security + rn_security + flutter_security
    
    for pattern, description in all_security:
        if re.search(pattern, content, re.IGNORECASE):
            security_issues.append(f"🔒 {description}")
    
    if len(security_issues) >= 2:
        return "HIGH", security_issues
    elif security_issues:
        return "MEDIUM", security_issues
    
    return "NONE", []

def check_mobile_ui_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for mobile UI/UX best practices"""
    
    ui_issues = []
    
    # Accessibility patterns
    accessibility_patterns = [
        (r'Button.*accessibilityLabel.*nil|Button\(.*\).*{', "Missing accessibility labels for buttons"),
        (r'Image.*contentDescription.*null|Image\(.*\)', "Missing content descriptions for images"),
        (r'TouchableOpacity.*accessibilityRole.*undefined', "RN: Missing accessibility roles"),
        (r'Text.*fontSize.*[56789]\d+', "Font size too large (>50) - may cause layout issues"),
        (r'Text.*fontSize.*[1-9]\.', "Font size too small (<10) - accessibility concern"),
    ]
    
    # Layout patterns
    layout_patterns = [
        (r'position.*absolute.*top.*\d+.*left.*\d+', "Hardcoded absolute positioning - responsive issues"),
        (r'width.*\d+.*height.*\d+.*View', "Fixed dimensions - responsive design concern"),
        (r'ScrollView.*horizontal.*vertical', "Conflicting scroll directions - UX issue"),
        (r'FlatList.*horizontal.*showsVerticalScrollIndicator', "Inconsistent scroll indicators"),
    ]
    
    # Platform-specific patterns
    platform_patterns = [
        (r'Platform\.OS.*ios.*backgroundColor.*blue', "iOS: Blue background may conflict with system colors"),
        (r'Platform\.OS.*android.*elevation.*[0-9]{2,}', "Android: High elevation values - may cause shadows overlap"),
        (r'StatusBar.*backgroundColor.*android.*barStyle.*ios', "Mixed platform status bar styling"),
    ]
    
    all_ui_patterns = accessibility_patterns + layout_patterns + platform_patterns
    
    for pattern, description in all_ui_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            ui_issues.append(f"📱 {description}")
    
    if len(ui_issues) >= 3:
        return "MEDIUM", ui_issues
    elif ui_issues:
        return "LOW", ui_issues
    
    return "NONE", []

def check_mobile_memory_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for memory management issues"""
    
    memory_issues = []
    
    # iOS Memory patterns
    ios_memory = [
        (r'strong.*self.*completion', "iOS: Strong self reference in completion - potential retain cycle"),
        (r'@IBOutlet.*strong', "iOS: Strong IBOutlet reference - should be weak"),
        (r'Timer.*scheduledTimer.*self', "iOS: Timer with strong self reference - retain cycle"),
        (r'NotificationCenter.*addObserver.*self.*removeObserver', "iOS: Observer not removed - memory leak"),
    ]
    
    # Android Memory patterns
    android_memory = [
        (r'static.*Context|static.*Activity', "Android: Static context reference - memory leak"),
        (r'Handler.*Activity.*Message', "Android: Handler holding Activity reference - leak potential"),
        (r'AsyncTask.*Activity.*onPostExecute', "Android: AsyncTask holding Activity - rotation leak"),
        (r'Bitmap.*createBitmap.*recycle', "Android: Bitmap not recycled - memory usage"),
    ]
    
    # React Native Memory
    rn_memory = [
        (r'useEffect.*\[\].*return.*clearInterval', "RN: Missing cleanup in useEffect - memory leak"),
        (r'Animated\.timing.*start.*loop.*true', "RN: Looping animation without stop condition"),
        (r'setInterval.*this\.state.*componentWillUnmount', "RN: Interval not cleared on unmount"),
    ]
    
    all_memory = ios_memory + android_memory + rn_memory
    
    for pattern, description in all_memory:
        if re.search(pattern, content, re.IGNORECASE):
            memory_issues.append(f"💾 {description}")
    
    if len(memory_issues) >= 2:
        return "HIGH", memory_issues
    elif memory_issues:
        return "MEDIUM", memory_issues
    
    return "NONE", []

def get_mobile_recommendations(content: str, file_path: str) -> list:
    """Get mobile development recommendations"""
    
    recommendations = []
    
    # Testing recommendations
    if not re.search(r'test|spec|XCTest|@Test|jest', content.lower()) and len(content) > 1000:
        recommendations.append("🧪 Add unit tests for mobile components and business logic")
    
    # Performance monitoring
    if re.search(r'network|api|fetch|URLSession', content, re.IGNORECASE):
        recommendations.append("📊 Consider adding performance monitoring for network operations")
    
    # Offline capability
    if re.search(r'fetch|axios|URLSession', content, re.IGNORECASE) and 'offline' not in content.lower():
        recommendations.append("📶 Consider offline capability and network error handling")
    
    # Platform optimization
    if 'Platform.OS' in content and re.search(r'ios.*android|android.*ios', content):
        recommendations.append("🎯 Optimize platform-specific code for better performance")
    
    # Accessibility
    if not re.search(r'accessibility|a11y|contentDescription|accessibilityLabel', content):
        recommendations.append("♿ Add accessibility support for inclusive user experience")
    
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
        
        # Skip if no content or not mobile-related
        if not content:
            sys.exit(0)
        
        # Check if content is mobile-related
        mobile_extensions = ['.swift', '.kt', '.js', '.jsx', '.ts', '.tsx', '.dart']
        mobile_keywords = ['UIKit', 'SwiftUI', 'Activity', 'Fragment', 'React', 'Native', 'Flutter', 'Widget']
        
        is_mobile_file = any(ext in file_path for ext in mobile_extensions)
        has_mobile_content = any(keyword in content for keyword in mobile_keywords)
        
        if not (is_mobile_file or has_mobile_content):
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Mobile development analysis
        perf_risk, perf_issues = check_mobile_performance_patterns(content, file_path)
        security_risk, security_issues = check_mobile_security_patterns(content, file_path)
        ui_risk, ui_issues = check_mobile_ui_patterns(content, file_path)
        memory_risk, memory_issues = check_mobile_memory_patterns(content, file_path)
        recommendations = get_mobile_recommendations(content, file_path)
        
        # Determine overall risk
        all_risks = [perf_risk, security_risk, ui_risk, memory_risk]
        if "HIGH" in all_risks:
            overall_risk = "HIGH"
        elif "MEDIUM" in all_risks:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Block on memory leaks and security issues
        if memory_risk == "HIGH" or security_risk == "HIGH":
            critical_issues = []
            if memory_risk == "HIGH":
                critical_issues.extend([f"• {issue}" for issue in memory_issues])
            if security_risk == "HIGH":
                critical_issues.extend([f"• {issue}" for issue in security_issues])
            
            issue_details = "\n".join(critical_issues)
            HookUtils.block_with_error(f"🚫 CRITICAL MOBILE ISSUES - OPERATION BLOCKED\n\n{issue_details}\n\nFile: {file_path}\n\nFix memory leaks and security vulnerabilities before proceeding.")
        
        # Human confirmation for performance issues
        if overall_risk == "HIGH" or (overall_risk == "MEDIUM" and perf_risk == "MEDIUM"):
            all_issues = perf_issues + security_issues + ui_issues + memory_issues
            issue_text = "\n".join([f"• {issue}" for issue in all_issues[:5]])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"📱 MOBILE DEVELOPMENT REVIEW\n\n{issue_text}\n\nFile: {file_path}\n\nPlease review these mobile development concerns."
                }
            })
        
        # Success with mobile insights
        success_msg = "✅ Mobile validation completed"
        
        if overall_risk == "MEDIUM" and memory_risk != "HIGH" and security_risk != "HIGH":
            insights = []
            insights.extend([f"💡 {issue}" for issue in perf_issues[:2]])
            insights.extend([f"💡 {issue}" for issue in ui_issues[:1]])
            
            if insights:
                insight_text = "\n".join(insights)
                success_msg += f"\n\nMobile Insights:\n{insight_text}"
        
        if recommendations and overall_risk == "LOW":
            rec_text = "\n".join([f"📱 {rec}" for rec in recommendations[:3]])
            success_msg += f"\n\nRecommendations:\n{rec_text}"
        
        suppress_output = (overall_risk == "LOW" and not recommendations and not has_mobile_content)
        HookUtils.allow_with_message(success_msg, suppress=suppress_output)
        
    except Exception as e:
        print(f"Mobile hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
