#!/usr/bin/env python3
"""
Data Science and AI hooks for data-scientist, ml-engineer, ai-researcher, data-analyst
Validates data processing, model development, and ML best practices
"""

import json
import sys
import os
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from hook_utils import HookUtils, WorkStatusManager, OrchestrationManager

def check_data_quality_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for data quality and validation issues"""
    
    data_issues = []
    
    # Data loading patterns
    loading_patterns = [
        (r'pd\.read_csv\([^)]*\)(?!.*na_values)', "Pandas: read_csv without na_values - missing data handling"),
        (r'pd\.read_csv\([^)]*\)(?!.*dtype)', "Pandas: read_csv without dtype specification - memory inefficiency"),
        (r'\.dropna\(\)(?!.*subset)', "Pandas: dropna() without subset - may remove too much data"),
        (r'\.fillna\(0\)(?!.*method)', "Pandas: fillna(0) without method - may introduce bias"),
        (r'df\[.*\]\.values(?!.*copy)', "Pandas: .values without copy() - may cause view issues"),
    ]
    
    # Data validation patterns
    validation_patterns = [
        (r'df\.shape(?!.*print|.*log)', "Data: Checking shape without logging - missing data validation"),
        (r'df\.head\(\)(?!.*print|.*display)', "Data: head() without display - missing data inspection"),
        (r'df\.isnull\(\)(?!.*sum|.*any)', "Data: isnull() without aggregation - incomplete null check"),
        (r'df\.duplicated\(\)(?!.*sum|.*any)', "Data: duplicated() without aggregation - incomplete duplicate check"),
        (r'df.*==.*df.*(?!.*all|.*any)', "Data: DataFrame comparison without all()/any() - boolean array"),
    ]
    
    # Statistical patterns
    stats_patterns = [
        (r'\.mean\(\)(?!.*axis)', "Stats: mean() without axis specification - may aggregate incorrectly"),
        (r'np\.random\.seed\(\d+\)(?!.*reproducib)', "Random: Fixed seed without documentation - reproducibility concern"),
        (r'train_test_split(?!.*random_state)', "ML: train_test_split without random_state - not reproducible"),
        (r'\.sample\((?!.*random_state)', "Sampling: sample() without random_state - not reproducible"),
    ]
    
    all_patterns = loading_patterns + validation_patterns + stats_patterns
    
    for pattern, description in all_patterns:
        if re.search(pattern, content):
            data_issues.append(f"📊 {description}")
    
    if len(data_issues) >= 4:
        return "MEDIUM", data_issues
    elif len(data_issues) >= 2:
        return "LOW", data_issues
    
    return "NONE", []

def check_ml_model_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for machine learning model issues"""
    
    ml_issues = []
    
    # Model training patterns
    training_patterns = [
        (r'\.fit\(X.*y\)(?!.*validation)', "ML: fit() without validation - no overfitting check"),
        (r'GridSearchCV(?!.*cv=)', "ML: GridSearchCV without explicit CV - default may not be appropriate"),
        (r'RandomForestClassifier\(\)(?!.*n_estimators)', "ML: RandomForest without n_estimators - using default"),
        (r'\.predict\((?!.*reshape|.*values)', "ML: predict() on raw data - may need preprocessing"),
        (r'accuracy_score(?!.*average)', "ML: accuracy_score without average parameter for multiclass"),
    ]
    
    # Feature engineering patterns
    feature_patterns = [
        (r'StandardScaler\(\)\.fit_transform\(X\)(?!.*train)', "ML: StandardScaler on full dataset - data leakage"),
        (r'LabelEncoder\(\)\.fit_transform(?!.*train)', "ML: LabelEncoder on full dataset - data leakage"),
        (r'df\.get_dummies\((?!.*drop_first)', "ML: get_dummies without drop_first - multicollinearity"),
        (r'from sklearn\.preprocessing import \*', "ML: Wildcard sklearn imports - namespace pollution"),
    ]
    
    # Model evaluation patterns
    evaluation_patterns = [
        (r'\.score\(X.*y\)(?!.*cross_val)', "ML: model.score() without cross-validation - single metric"),
        (r'confusion_matrix(?!.*normalize)', "ML: confusion_matrix without normalization - hard to interpret"),
        (r'classification_report(?!.*target_names)', "ML: classification_report without target_names"),
        (r'roc_auc_score(?!.*multi_class)', "ML: roc_auc_score for multiclass without multi_class parameter"),
    ]
    
    all_ml_patterns = training_patterns + feature_patterns + evaluation_patterns
    
    for pattern, description in all_ml_patterns:
        if re.search(pattern, content):
            ml_issues.append(f"🤖 {description}")
    
    if len(ml_issues) >= 3:
        return "MEDIUM", ml_issues
    elif ml_issues:
        return "LOW", ml_issues
    
    return "NONE", []

def check_data_leakage_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for data leakage issues"""
    
    leakage_issues = []
    
    # Time series leakage
    time_patterns = [
        (r'train_test_split.*shuffle=True.*time|date', "LEAKAGE: Shuffling time series data - future information leak"),
        (r'\.sort_values.*train_test_split(?!.*shuffle=False)', "LEAKAGE: Sorting before split without shuffle=False"),
        (r'pd\.to_datetime.*train_test_split.*shuffle=True', "LEAKAGE: Time data with shuffle=True - temporal order lost"),
    ]
    
    # Target leakage
    target_patterns = [
        (r'X.*=.*df.*y.*=.*df.*X.*y', "LEAKAGE: Features include target variable"),
        (r'StandardScaler.*fit.*X.*y.*transform.*X_test', "LEAKAGE: Scaler fitted on target - indirect information"),
        (r'df\.corr\(\).*target.*\.drop.*target', "LEAKAGE: Feature selection using target correlation on full dataset"),
    ]
    
    # Cross-validation leakage
    cv_patterns = [
        (r'cross_val_score.*StandardScaler.*fit_transform', "LEAKAGE: Preprocessing before CV - information leak"),
        (r'SelectKBest.*fit.*cross_val_score', "LEAKAGE: Feature selection before CV - selection bias"),
        (r'SMOTE.*fit_resample.*cross_val_score', "LEAKAGE: SMOTE before CV - data generation bias"),
    ]
    
    all_leakage = time_patterns + target_patterns + cv_patterns
    
    for pattern, description in all_leakage:
        if re.search(pattern, content):
            leakage_issues.append(f"🔐 {description}")
    
    if len(leakage_issues) >= 1:
        return "HIGH", leakage_issues
    
    return "NONE", []

def check_data_privacy_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for data privacy and ethical issues"""
    
    privacy_issues = []
    
    # PII patterns
    pii_patterns = [
        (r'df.*name.*email.*phone', "PRIVACY: PII columns detected - ensure anonymization"),
        (r'social.*security|ssn', "PRIVACY: SSN data detected - high sensitivity"),
        (r'credit.*card|payment.*info', "PRIVACY: Payment data detected - PCI compliance required"),
        (r'medical.*record|health.*data', "PRIVACY: Health data detected - HIPAA compliance required"),
    ]
    
    # Data export patterns
    export_patterns = [
        (r'\.to_csv\(.*personal|\.to_excel\(.*personal', "PRIVACY: Exporting personal data - review data handling"),
        (r'plt\.savefig.*personal|sns\..*personal', "PRIVACY: Visualizing personal data - anonymize before plotting"),
        (r'print\(df.*personal\)|display\(df.*personal\)', "PRIVACY: Displaying personal data - potential exposure"),
    ]
    
    # Bias patterns
    bias_patterns = [
        (r'gender.*==.*male.*female', "ETHICS: Gender binary assumption - consider inclusivity"),
        (r'race.*ethnicity.*model', "ETHICS: Race/ethnicity features - potential discrimination"),
        (r'age.*>\s*\d+.*reject|age.*<\s*\d+.*reject', "ETHICS: Age-based filtering - potential age discrimination"),
    ]
    
    all_privacy = pii_patterns + export_patterns + bias_patterns
    
    for pattern, description in all_privacy:
        if re.search(pattern, content, re.IGNORECASE):
            privacy_issues.append(f"🔒 {description}")
    
    if len(privacy_issues) >= 2:
        return "HIGH", privacy_issues
    elif privacy_issues:
        return "MEDIUM", privacy_issues
    
    return "NONE", []

def check_performance_patterns(content: str, file_path: str) -> tuple[str, list]:
    """Check for data processing performance issues"""
    
    performance_issues = []
    
    # Pandas performance patterns
    pandas_perf = [
        (r'for.*in.*df\.iterrows\(\)', "PERFORMANCE: iterrows() is slow - use vectorized operations or itertuples()"),
        (r'df\.apply.*lambda.*axis=1', "PERFORMANCE: apply with lambda on rows - slow for large datasets"),
        (r'pd\.concat.*for.*in.*loop', "PERFORMANCE: concat in loop - collect then concat once"),
        (r'df\[df\[.*\] == .*\]\[df\[.*\] == .*\]', "PERFORMANCE: Multiple boolean indexing - combine conditions"),
        (r'df\.groupby.*\.apply.*lambda', "PERFORMANCE: groupby.apply with lambda - consider agg() or transform()"),
    ]
    
    # NumPy performance patterns
    numpy_perf = [
        (r'for.*in.*range.*arr\[i\]', "PERFORMANCE: Manual array iteration - use vectorized operations"),
        (r'np\.append.*for.*in', "PERFORMANCE: np.append in loop - preallocate array"),
        (r'list\(arr\).*for.*in', "PERFORMANCE: Converting array to list in loop - unnecessary overhead"),
    ]
    
    # Memory patterns
    memory_patterns = [
        (r'df\.copy\(\)(?!.*deep=False)', "MEMORY: Deep copy without necessity - memory usage"),
        (r'pd\.read_csv.*chunksize(?!.*iterator)', "MEMORY: chunksize without iterator - not processing chunks"),
        (r'np\.zeros\(\d{6,}\)', "MEMORY: Large array allocation - consider memory constraints"),
    ]
    
    all_perf = pandas_perf + numpy_perf + memory_patterns
    
    for pattern, description in all_perf:
        if re.search(pattern, content):
            performance_issues.append(f"⚡ {description}")
    
    if len(performance_issues) >= 3:
        return "MEDIUM", performance_issues
    elif performance_issues:
        return "LOW", performance_issues
    
    return "NONE", []

def get_data_science_recommendations(content: str, file_path: str) -> list:
    """Get data science recommendations"""
    
    recommendations = []
    
    # Documentation recommendations
    if not re.search(r'""".*"""', content, re.DOTALL) and len(content) > 500:
        recommendations.append("📚 Add docstrings documenting data sources, assumptions, and methodology")
    
    # Reproducibility recommendations
    if 'random' in content.lower() and 'seed' not in content.lower():
        recommendations.append("🔄 Set random seeds for reproducible results")
    
    # Version control recommendations
    if re.search(r'\.pkl|\.joblib|\.h5|\.model', content):
        recommendations.append("📦 Use model versioning and MLOps practices for model artifacts")
    
    # Testing recommendations
    if not re.search(r'assert|test|Test', content) and 'def ' in content:
        recommendations.append("🧪 Add unit tests for data processing functions")
    
    # Monitoring recommendations
    if re.search(r'model\.predict|\.score\(', content):
        recommendations.append("📊 Add model performance monitoring and drift detection")
    
    # Data validation recommendations
    if 'pd.read_' in content and 'assert' not in content:
        recommendations.append("✅ Add data quality assertions and validation checks")
    
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
        
        # Check if content is data science related
        ds_keywords = ['pandas', 'numpy', 'sklearn', 'tensorflow', 'pytorch', 'matplotlib', 'seaborn', 'jupyter', 'pd.', 'np.', 'plt.']
        has_ds_content = any(keyword in content.lower() for keyword in ds_keywords)
        
        if not has_ds_content:
            sys.exit(0)
        
        work_status = WorkStatusManager(project_dir)
        orchestration = OrchestrationManager(project_dir)
        
        # Check file locks
        if file_path:
            is_locked, lock_info = work_status.is_file_locked(file_path)
            if is_locked:
                HookUtils.block_with_error(f"🔒 FILE LOCKED: {lock_info}")
        
        # Data science analysis
        data_risk, data_issues = check_data_quality_patterns(content, file_path)
        ml_risk, ml_issues = check_ml_model_patterns(content, file_path)
        leakage_risk, leakage_issues = check_data_leakage_patterns(content, file_path)
        privacy_risk, privacy_issues = check_data_privacy_patterns(content, file_path)
        perf_risk, perf_issues = check_performance_patterns(content, file_path)
        recommendations = get_data_science_recommendations(content, file_path)
        
        # Determine overall risk
        all_risks = [data_risk, ml_risk, leakage_risk, privacy_risk, perf_risk]
        if "HIGH" in all_risks:
            overall_risk = "HIGH"
        elif "MEDIUM" in all_risks:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Block on data leakage and privacy violations
        if leakage_risk == "HIGH" or privacy_risk == "HIGH":
            critical_issues = []
            if leakage_risk == "HIGH":
                critical_issues.extend([f"• {issue}" for issue in leakage_issues])
            if privacy_risk == "HIGH":
                critical_issues.extend([f"• {issue}" for issue in privacy_issues])
            
            issue_details = "\n".join(critical_issues)
            issue_type = "DATA LEAKAGE" if leakage_risk == "HIGH" else "PRIVACY VIOLATION"
            HookUtils.block_with_error(f"🚫 {issue_type} DETECTED - OPERATION BLOCKED\n\n{issue_details}\n\nFile: {file_path}\n\nFix these critical data science issues before proceeding.")
        
        # Human confirmation for medium-high risk data science issues
        if overall_risk == "HIGH" or (overall_risk == "MEDIUM" and (ml_risk == "MEDIUM" or privacy_risk == "MEDIUM")):
            all_issues = data_issues + ml_issues + leakage_issues + privacy_issues + perf_issues
            issue_text = "\n".join([f"• {issue}" for issue in all_issues[:5]])
            HookUtils.output_json({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"📊 DATA SCIENCE REVIEW\n\n{issue_text}\n\nFile: {file_path}\n\nPlease review these data science and ML concerns."
                }
            })
        
        # Success with data science insights
        success_msg = "✅ Data science validation completed"
        
        if overall_risk == "MEDIUM" and leakage_risk != "HIGH" and privacy_risk != "HIGH":
            insights = []
            insights.extend([f"💡 {issue}" for issue in data_issues[:2]])
            insights.extend([f"💡 {issue}" for issue in ml_issues[:2]])
            
            if insights:
                insight_text = "\n".join(insights)
                success_msg += f"\n\nData Science Insights:\n{insight_text}"
        
        if recommendations and overall_risk == "LOW":
            rec_text = "\n".join([f"📊 {rec}" for rec in recommendations[:3]])
            success_msg += f"\n\nRecommendations:\n{rec_text}"
        
        suppress_output = (overall_risk == "LOW" and not recommendations)
        HookUtils.allow_with_message(success_msg, suppress=suppress_output)
        
    except Exception as e:
        print(f"Data science hook error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
