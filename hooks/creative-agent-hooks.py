#!/usr/bin/env python3
"""
Creative and content hooks for ui-ux-designer, technical-writer, content-strategist, brand-specialist
Validates design systems, content quality, and creative asset management
"""

import json
import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def check_design_system_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for design system and UI consistency issues"""
    
    design_issues = []
    
    # CSS/SCSS design patterns
    css_patterns = [
        (r'color:\s*#[0-9a-fA-F]{6}(?!.*var\()', "DESIGN: Hardcoded hex colors - use CSS variables for consistency"),
        (r'font-size:\s*\d+px(?!.*var\()', "DESIGN: Hardcoded font sizes - use design system scale"),
        (r'margin:\s*\d+px.*margin:\s*\d+px', "DESIGN: Inconsistent margin values - standardize spacing"),
        (r'padding:\s*\d+px.*padding:\s*\d+px', "DESIGN: Inconsistent padding values - standardize spacing"),
        (r'border-radius:\s*\d+px(?!.*var\()', "DESIGN: Hardcoded border radius - use design tokens"),
        (r'box-shadow:\s*[^;]+(?!.*var\()', "DESIGN: Custom shadows - use elevation system"),
        (r'z-index:\s*\d{3,}', "DESIGN: High z-index values - review stacking context"),
    ]
    
    # React/Component patterns
    react_patterns = [
        (r'style=\{\{[^}]*color:\s*[\'"][#a-zA-Z]', "REACT: Inline color styles - use design system"),
        (r'className.*btn.*className.*button', "REACT: Inconsistent button class naming"),
        (r'<div.*style=.*backgroundColor', "REACT: Inline background colors - use CSS classes"),
        (r'fontSize:\s*\d+(?!.*theme)', "REACT: Hardcoded font sizes in JSX - use theme"),
    ]
    
    # Accessibility patterns
    a11y_patterns = [
        (r'<img(?!.*alt=)', "A11Y: Image without alt attribute - accessibility violation"),
        (r'<button(?!.*aria-label|.*title)', "A11Y: Button without accessible name - screen reader issue"),
        (r'onClick.*<div(?!.*role=)', "A11Y: Click handler on div without role - keyboard accessibility"),
        (r'color.*contrast.*ratio', "A11Y: Color contrast mentioned - ensure WCAG compliance"),
        (r'font-size:\s*[1-9]px', "A11Y: Font size below 10px - readability concern"),
    ]
    
    all_design = css_patterns + react_patterns + a11y_patterns
    
    for pattern, description in all_design:
        if re.search(pattern, content):
            design_issues.append(f"🎨 {description}")
    
    if len(design_issues) >= 4:
        return "MEDIUM", design_issues
    elif len(design_issues) >= 2:
        return "LOW", design_issues
    
    return "NONE", []

def check_content_quality_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for content quality and writing issues"""
    
    content_issues = []
    
    # Writing quality patterns
    writing_patterns = [
        (r'\b(very|really|quite|pretty)\s+\w+', "WRITING: Weak qualifiers - use stronger, specific language"),
        (r'\.{3,}', "WRITING: Excessive ellipses - improve sentence structure"),
        (r'\b(thing|stuff|things)\b', "WRITING: Vague terms - be more specific"),
        (r'\b(obviously|clearly|simply)\b', "WRITING: Assumptive language - may alienate readers"),
        (r'!!+', "WRITING: Multiple exclamation marks - reduce emphasis"),
        (r'\b(click here|read more|learn more)\b', "WRITING: Generic link text - use descriptive links"),
    ]
    
    # Technical writing patterns
    tech_writing_patterns = [
        (r'we\s+(recommend|suggest|advise)', "TECH WRITING: 'We recommend' - use active voice"),
        (r'you\s+(should|must|need to)', "TECH WRITING: Prescriptive language - consider softer alternatives"),
        (r'simply\s+(do|use|add)', "TECH WRITING: 'Simply' assumes ease - may not be simple for users"),
        (r'just\s+(add|remove|change)', "TECH WRITING: 'Just' minimizes complexity - acknowledge difficulty"),
        (r'easy|simple|straightforward', "TECH WRITING: Subjective difficulty - let users judge complexity"),
    ]
    
    # Documentation patterns
    docs_patterns = [
        (r'TODO:.*documentation', "DOCS: TODO for documentation - incomplete content"),
        (r'FIXME:.*content', "DOCS: FIXME for content - needs revision"),
        (r'lorem ipsum', "DOCS: Lorem ipsum placeholder - replace with real content"),
        (r'example\.com|test\.example', "DOCS: Example.com in production docs - use real examples"),
        (r'INSERT_.*_HERE', "DOCS: Placeholder text - replace with actual content"),
    ]
    
    all_content = writing_patterns + tech_writing_patterns + docs_patterns
    
    for pattern, description in all_content:
        if re.search(pattern, content, re.IGNORECASE):
            content_issues.append(f"📝 {description}")
    
    if len(content_issues) >= 4:
        return "MEDIUM", content_issues
    elif len(content_issues) >= 2:
        return "LOW", content_issues
    
    return "NONE", []

def check_brand_consistency_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for brand consistency issues"""
    
    brand_issues = []
    
    # Brand voice patterns
    voice_patterns = [
        (r'awesome|amazing|incredible', "BRAND: Superlative overuse - may weaken brand voice"),
        (r'we\'re\s+excited|thrilled|delighted', "BRAND: Emotional language - ensure brand voice consistency"),
        (r'revolutionar(y|ize)|cutting-edge|state-of-the-art', "BRAND: Buzzwords - consider more authentic language"),
        (r'industry[- ]leading|best-in-class|world-class', "BRAND: Unsubstantiated claims - provide evidence"),
    ]
    
    # Typography patterns
    typography_patterns = [
        (r'font-family:.*Arial.*font-family:.*Helvetica', "BRAND: Mixed fonts - establish typography hierarchy"),
        (r'font-weight:\s*bold.*font-weight:\s*\d00', "BRAND: Inconsistent font weights - standardize weight scale"),
        (r'text-transform:\s*uppercase.*text-transform:\s*lowercase', "BRAND: Mixed text transforms - establish text casing rules"),
    ]
    
    # Color brand patterns
    color_patterns = [
        (r'#ff0000|red.*#00ff00|green', "BRAND: Primary colors - ensure brand color palette"),
        (r'color:.*blue.*color:.*blue', "BRAND: Multiple blue shades - standardize color system"),
        (r'background.*gradient.*background.*gradient', "BRAND: Multiple gradients - establish gradient system"),
    ]
    
    all_brand = voice_patterns + typography_patterns + color_patterns
    
    for pattern, description in all_brand:
        if re.search(pattern, content, re.IGNORECASE):
            brand_issues.append(f"🏷️ {description}")
    
    if len(brand_issues) >= 3:
        return "MEDIUM", brand_issues
    elif brand_issues:
        return "LOW", brand_issues
    
    return "NONE", []

def check_asset_management_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for creative asset management issues"""
    
    asset_issues = []
    
    # Image optimization patterns
    image_patterns = [
        (r'\.jpg|\.png.*width.*height.*\d{4,}', "ASSETS: Large image dimensions - optimize for web"),
        (r'background-image.*url\(.*\.jpg\)', "ASSETS: JPG for UI elements - consider SVG or PNG"),
        (r'<img.*src.*\.bmp|\.tiff', "ASSETS: Unoptimized image format - use web formats"),
        (r'data:image/.*base64.*[A-Za-z0-9+/]{1000,}', "ASSETS: Large base64 images - use external files"),
    ]
    
    # SVG patterns
    svg_patterns = [
        (r'<svg.*width="\d{3,}".*height="\d{3,}"', "ASSETS: Large SVG dimensions - optimize viewBox"),
        (r'<svg(?!.*viewBox)', "ASSETS: SVG without viewBox - scalability issue"),
        (r'fill="#\w+".*fill="#\w+".*svg', "ASSETS: Hardcoded SVG colors - use CSS for theming"),
    ]
    
    # Font patterns
    font_patterns = [
        (r'@import.*fonts\.googleapis\.com.*@import', "ASSETS: Multiple font imports - combine requests"),
        (r'font-display:.*swap.*font-display:.*block', "ASSETS: Inconsistent font display - standardize loading"),
        (r'woff2|woff.*ttf|otf', "ASSETS: Mixed font formats - prioritize modern formats"),
    ]
    
    all_assets = image_patterns + svg_patterns + font_patterns
    
    for pattern, description in all_assets:
        if re.search(pattern, content):
            asset_issues.append(f"🖼️ {description}")
    
    if len(asset_issues) >= 2:
        return "MEDIUM", asset_issues
    elif asset_issues:
        return "LOW", asset_issues
    
    return "NONE", []

def get_creative_recommendations(content: str, file_path: str) -> list:
    """Get creative and content recommendations"""
    
    recommendations = []
    
    # Design system recommendations
    if re.search(r'color:|background-color:|border-color:', content) and not re.search(r'var\(--', content):
        recommendations.append("🎨 Implement CSS custom properties for consistent design tokens")
    
    # Content strategy recommendations
    if re.search(r'<h[1-6]>.*<h[1-6]>', content) and not re.search(r'aria-level|role=', content):
        recommendations.append("📋 Implement proper heading hierarchy for SEO and accessibility")
    
    # Performance recommendations
    if re.search(r'\.jpg|\.png.*\d{3,}', content):
        recommendations.append("⚡ Optimize images with modern formats (WebP, AVIF) and lazy loading")
    
    # Accessibility recommendations
    if re.search(r'color.*#[0-9a-fA-F]{6}', content) and 'contrast' not in content.lower():
        recommendations.append("♿ Validate color contrast ratios for WCAG compliance")
    
    # Internationalization recommendations
    if re.search(r'text-align:\s*(left|right)', content) and 'rtl' not in content.lower():
        recommendations.append("🌍 Consider right-to-left (RTL) language support in text alignment")
    
    # Version control recommendations
    if re.search(r'\.psd|\.ai|\.sketch|\.fig', file_path):
        recommendations.append("📦 Use design version control for binary design files")
    
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
        
        # Check if content is creative/content related
        creative_extensions = ['.css', '.scss', '.sass', '.html', '.jsx', '.tsx', '.md', '.mdx', '.svg']
        creative_keywords = ['style', 'design', 'content', 'brand', 'font', 'color', 'margin', 'padding', 'css', 'html']
        
        is_creative_file = any(ext in file_path for ext in creative_extensions)
        has_creative_content = any(keyword in content.lower() for keyword in creative_keywords)
        
        if not (is_creative_file or has_creative_content):
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Creative and content analysis
        design_risk, design_issues = check_design_system_patterns(content, file_path)
        content_risk, content_issues = check_content_quality_patterns(content, file_path)
        brand_risk, brand_issues = check_brand_consistency_patterns(content, file_path)
        asset_risk, asset_issues = check_asset_management_patterns(content, file_path)
        recommendations = get_creative_recommendations(content, file_path)
        
        # Determine overall risk
        all_risks = [design_risk, content_risk, brand_risk, asset_risk]
        if "HIGH" in all_risks:
            overall_risk = "HIGH"
        elif "MEDIUM" in all_risks:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Human confirmation for creative consistency issues
        if overall_risk == "MEDIUM":
            all_issues = design_issues + content_issues + brand_issues + asset_issues
            issue_text = "\n".join([f"• {issue}" for issue in all_issues[:6]])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"🎨 CREATIVE REVIEW\n\n{issue_text}\n\nFile: {file_path}\n\nPlease review these creative and content consistency concerns."
                }
            })
        
        # Success with creative insights
        success_msg = "✅ Creative validation completed"
        
        if overall_risk == "LOW" and any([design_issues, content_issues, brand_issues, asset_issues]):
            insights = []
            insights.extend([f"💡 {issue}" for issue in design_issues[:2]])
            insights.extend([f"💡 {issue}" for issue in content_issues[:2]])
            insights.extend([f"💡 {issue}" for issue in brand_issues[:1]])
            
            if insights:
                insight_text = "\n".join(insights)
                success_msg += f"\n\nCreative Insights:\n{insight_text}"
        
        if recommendations and overall_risk == "LOW":
            rec_text = "\n".join([f"🎨 {rec}" for rec in recommendations[:3]])
            success_msg += f"\n\nRecommendations:\n{rec_text}"
        
        suppress_output = (overall_risk == "LOW" and not recommendations and not has_creative_content)
        HookUtils.allow_with_message(success_msg, suppress=suppress_output)
        
    except Exception as e:
        print(f"Creative hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
