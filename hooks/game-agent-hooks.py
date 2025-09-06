#!/usr/bin/env python3
"""
Game development hooks for unity-expert, unreal-expert, game-designer, game-developer
Validates game performance, mechanics, and development best practices
"""

import json
import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def check_game_performance_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for game performance anti-patterns"""
    
    performance_issues = []
    
    # Unity C# patterns
    unity_patterns = [
        (r'Update\(\).*GameObject\.Find|Update\(\).*FindObjectOfType', "Unity: GameObject.Find in Update() - cache references"),
        (r'Update\(\).*GetComponent', "Unity: GetComponent in Update() - cache component references"),
        (r'Update\(\).*Instantiate.*Destroy', "Unity: Instantiate/Destroy in Update() - use object pooling"),
        (r'foreach.*GameObject.*FindObjectsOfType', "Unity: FindObjectsOfType in loop - expensive operation"),
        (r'OnGUI\(\).*GUI\..*for.*in', "Unity: Complex GUI operations in OnGUI() - use UI system"),
        (r'String\.Concat.*\+.*Update\(\)', "Unity: String concatenation in Update() - causes GC pressure"),
        (r'new.*Vector3.*Update\(\)', "Unity: Vector3 allocation in Update() - cache or use static"),
    ]
    
    # Unreal C++ patterns
    unreal_patterns = [
        (r'Tick.*GetWorld\(\)->GetAllActorsOfClass', "Unreal: GetAllActorsOfClass in Tick - cache results"),
        (r'Tick.*FVector.*new', "Unreal: Vector allocation in Tick - use stack allocation"),
        (r'BeginPlay.*while.*true', "Unreal: Infinite loop in BeginPlay - will freeze game"),
        (r'UPROPERTY.*BlueprintReadWrite.*private', "Unreal: Private BlueprintReadWrite - inconsistent access"),
        (r'TArray.*Add.*RemoveAt.*for', "Unreal: TArray manipulation in tight loops - performance hit"),
    ]
    
    # General game patterns
    game_patterns = [
        (r'while.*true.*update|while.*true.*render', "Game: Infinite loop without frame limiting - CPU overuse"),
        (r'sleep\(\d+\).*game.*loop', "Game: Sleep in game loop - inconsistent frame timing"),
        (r'render.*for.*in.*objects.*\d{3,}', "Game: Rendering large object collections - batch operations"),
        (r'physics.*calculate.*\d+.*times', "Game: Excessive physics calculations - optimize timestep"),
    ]
    
    all_patterns = unity_patterns + unreal_patterns + game_patterns
    
    for pattern, description in all_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            performance_issues.append(f"🎮 {description}")
    
    if len(performance_issues) >= 3:
        return "HIGH", performance_issues
    elif len(performance_issues) >= 1:
        return "MEDIUM", performance_issues
    
    return "NONE", []

def check_game_memory_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for game memory management issues"""
    
    memory_issues = []
    
    # Unity memory patterns
    unity_memory = [
        (r'Resources\.Load.*Update\(\)', "Unity: Resources.Load in Update() - memory fragmentation"),
        (r'Instantiate.*gameObject.*Destroy.*null', "Unity: Missing null check after Destroy - memory reference"),
        (r'StartCoroutine.*while.*true.*yield.*null', "Unity: Infinite coroutine without break condition"),
        (r'OnDestroy.*StopAllCoroutines', "Unity: StopAllCoroutines in OnDestroy - may be too late"),
        (r'List<GameObject>.*Clear\(\).*Add\(.*Update', "Unity: List operations in Update() - GC pressure"),
    ]
    
    # Unreal memory patterns
    unreal_memory = [
        (r'NewObject.*BeginPlay.*EndPlay', "Unreal: Object creation without proper cleanup"),
        (r'UPROPERTY.*TArray.*UPROPERTY.*TArray.*class', "Unreal: Multiple large arrays - memory fragmentation"),
        (r'FString.*Append.*for.*in.*Tick', "Unreal: String operations in Tick - memory allocation"),
        (r'UGameInstance.*static.*TMap', "Unreal: Static containers in GameInstance - memory leak risk"),
    ]
    
    # General memory patterns
    general_memory = [
        (r'new.*\[\].*delete.*for.*i.*<.*1000', "Memory: Large array allocations in loops - fragment memory"),
        (r'malloc.*free.*game.*loop', "Memory: Manual memory management in game loop - error prone"),
        (r'std::vector.*reserve.*push_back.*erase', "Memory: Vector without proper capacity planning"),
    ]
    
    all_memory = unity_memory + unreal_memory + general_memory
    
    for pattern, description in all_memory:
        if re.search(pattern, content, re.IGNORECASE):
            memory_issues.append(f"💾 {description}")
    
    if len(memory_issues) >= 3:
        return "HIGH", memory_issues
    elif len(memory_issues) >= 1:
        return "MEDIUM", memory_issues
    
    return "NONE", []

def check_game_mechanics_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for game mechanics and design issues"""
    
    mechanics_issues = []
    
    # Physics and movement patterns
    physics_patterns = [
        (r'transform\.position.*=.*Input\.|rigidbody\.velocity.*Input\.', "Physics: Direct transform manipulation with input - bypasses physics"),
        (r'FixedUpdate\(\).*Time\.deltaTime', "Unity: Time.deltaTime in FixedUpdate - use fixedDeltaTime"),
        (r'Rigidbody\.velocity.*=.*new.*Vector3\(0.*0.*0\)', "Physics: Zeroing velocity directly - use physics methods"),
        (r'collision.*health.*--.*death', "Game: Direct health manipulation - missing validation"),
    ]
    
    # Game state patterns
    state_patterns = [
        (r'static.*bool.*gameState|static.*int.*score', "Game: Static game state - multiplayer issues"),
        (r'PlayerPrefs.*Save.*Update\(\)', "Unity: PlayerPrefs.Save in Update() - performance hit"),
        (r'if.*gameState.*==.*"playing".*gameState.*=.*"paused"', "Game: String-based state - error prone"),
        (r'public.*health.*public.*score.*class.*Player', "Game: Public game variables - encapsulation issue"),
    ]
    
    # Input patterns
    input_patterns = [
        (r'Input\.GetKey.*Update\(\).*Input\.GetKey', "Input: Multiple Input.GetKey calls - cache input state"),
        (r'Input\.mousePosition.*Screen\.width.*Update', "Input: Screen calculations in Update() - cache screen data"),
        (r'KeyCode\..*KeyCode\..*KeyCode\..*Update', "Input: Multiple key checks - use input mapping"),
    ]
    
    all_mechanics = physics_patterns + state_patterns + input_patterns
    
    for pattern, description in all_mechanics:
        if re.search(pattern, content, re.IGNORECASE):
            mechanics_issues.append(f"⚙️ {description}")
    
    if len(mechanics_issues) >= 3:
        return "MEDIUM", mechanics_issues
    elif mechanics_issues:
        return "LOW", mechanics_issues
    
    return "NONE", []

def check_game_audio_visual_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for audio and visual optimization patterns"""
    
    av_issues = []
    
    # Audio patterns
    audio_patterns = [
        (r'AudioSource\.Play\(\).*Update\(\)', "Audio: AudioSource.Play in Update() - audio spam"),
        (r'AudioClip.*Resources\.Load.*Play', "Audio: Loading audio clips synchronously - hitches"),
        (r'AudioSource.*volume.*Random\.Range.*Update', "Audio: Random volume changes in Update() - jarring"),
    ]
    
    # Visual patterns
    visual_patterns = [
        (r'Camera\.main\..*Update\(\)', "Unity: Camera.main access in Update() - cache camera reference"),
        (r'Renderer\.material.*Update\(\)', "Unity: Material access in Update() - creates instances"),
        (r'Light\.intensity.*Mathf\.Sin.*Update', "Unity: Light calculations in Update() - performance hit"),
        (r'Shader\.SetGlobalFloat.*Update\(\)', "Unity: Global shader properties in Update() - expensive"),
    ]
    
    # Rendering patterns
    rendering_patterns = [
        (r'Graphics\.DrawMesh.*for.*in.*Update', "Rendering: DrawMesh in loops - batch draw calls"),
        (r'Material.*new.*Material.*Renderer', "Rendering: Creating materials at runtime - memory leak"),
        (r'Texture2D.*SetPixel.*Apply.*Update', "Rendering: SetPixel operations in Update() - very slow"),
    ]
    
    all_av = audio_patterns + visual_patterns + rendering_patterns
    
    for pattern, description in all_av:
        if re.search(pattern, content, re.IGNORECASE):
            av_issues.append(f"🎨 {description}")
    
    if len(av_issues) >= 2:
        return "MEDIUM", av_issues
    elif av_issues:
        return "LOW", av_issues
    
    return "NONE", []

def get_game_recommendations(content: str, file_path: str) -> list:
    """Get game development recommendations"""
    
    recommendations = []
    
    # Performance recommendations
    if 'Update()' in content and not re.search(r'cache|static|readonly', content):
        recommendations.append("⚡ Cache frequently accessed components and references")
    
    # Object pooling recommendation
    if re.search(r'Instantiate.*Destroy', content, re.IGNORECASE):
        recommendations.append("🎯 Consider object pooling for frequently created/destroyed objects")
    
    # Testing recommendations
    if not re.search(r'test|Test|NUnit|GoogleTest', content) and len(content) > 1000:
        recommendations.append("🧪 Add unit tests for game mechanics and systems")
    
    # Documentation recommendations
    if re.search(r'class.*:.*MonoBehaviour|UCLASS', content) and not re.search(r'//.*@brief|///|/\*\*', content):
        recommendations.append("📚 Add documentation for game components and systems")
    
    # Profiling recommendations
    if re.search(r'performance|optimization|fps|frame', content.lower()):
        recommendations.append("📊 Use profiler tools to validate performance optimizations")
    
    # Version control recommendations
    if re.search(r'\.asset|\.prefab|\.scene', file_path):
        recommendations.append("🔄 Ensure binary assets are properly configured for version control")
    
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
        
        # Check if content is game development related
        game_extensions = ['.cs', '.cpp', '.h', '.hpp', '.js', '.cs', '.blueprint']
        game_keywords = ['Unity', 'Unreal', 'GameObject', 'MonoBehaviour', 'UCLASS', 'UPROPERTY', 'Update()', 'Tick']
        
        is_game_file = any(ext in file_path for ext in game_extensions)
        has_game_content = any(keyword in content for keyword in game_keywords)
        
        if not (is_game_file or has_game_content):
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Game development analysis
        perf_risk, perf_issues = check_game_performance_patterns(content, file_path)
        memory_risk, memory_issues = check_game_memory_patterns(content, file_path)
        mechanics_risk, mechanics_issues = check_game_mechanics_patterns(content, file_path)
        av_risk, av_issues = check_game_audio_visual_patterns(content, file_path)
        recommendations = get_game_recommendations(content, file_path)
        
        # Determine overall risk
        all_risks = [perf_risk, memory_risk, mechanics_risk, av_risk]
        if "HIGH" in all_risks:
            overall_risk = "HIGH"
        elif "MEDIUM" in all_risks:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Block on severe performance issues
        if perf_risk == "HIGH" or memory_risk == "HIGH":
            critical_issues = []
            if perf_risk == "HIGH":
                critical_issues.extend([f"• {issue}" for issue in perf_issues])
            if memory_risk == "HIGH":
                critical_issues.extend([f"• {issue}" for issue in memory_issues])
            
            issue_details = "\n".join(critical_issues)
            HookUtils.block_with_error(f"🚫 CRITICAL GAME PERFORMANCE ISSUES\n\n{issue_details}\n\nFile: {file_path}\n\nThese issues will cause severe performance problems. Fix before proceeding.")
        
        # Human confirmation for game development concerns
        if overall_risk == "HIGH" or (overall_risk == "MEDIUM" and (perf_risk == "MEDIUM" or mechanics_risk == "MEDIUM")):
            all_issues = perf_issues + memory_issues + mechanics_issues + av_issues
            issue_text = "\n".join([f"• {issue}" for issue in all_issues[:5]])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"🎮 GAME DEVELOPMENT REVIEW\n\n{issue_text}\n\nFile: {file_path}\n\nPlease review these game development concerns for performance and quality."
                }
            })
        
        # Success with game development insights
        success_msg = "✅ Game development validation completed"
        
        if overall_risk == "MEDIUM" and perf_risk != "HIGH" and memory_risk != "HIGH":
            insights = []
            insights.extend([f"💡 {issue}" for issue in mechanics_issues[:2]])
            insights.extend([f"💡 {issue}" for issue in av_issues[:1]])
            
            if insights:
                insight_text = "\n".join(insights)
                success_msg += f"\n\nGame Development Insights:\n{insight_text}"
        
        if recommendations and overall_risk == "LOW":
            rec_text = "\n".join([f"🎮 {rec}" for rec in recommendations[:3]])
            success_msg += f"\n\nRecommendations:\n{rec_text}"
        
        suppress_output = (overall_risk == "LOW" and not recommendations and not has_game_content)
        HookUtils.allow_with_message(success_msg, suppress=suppress_output)
        
    except Exception as e:
        print(f"Game development hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
