"""
Advanced Frequency Detection Module

Analyzes actual spacing and regularity patterns to determine message frequency,
not just counting occurrences.
"""

import pandas as pd
import numpy as np
from scipy import stats


def analyze_occurrence_pattern(dates):
    """
    Analyze the actual spacing between occurrences to determine frequency pattern

    Returns:
        - frequency_category: daily, weekly, biweekly, monthly, quarterly, semi_annual, irregular
        - confidence: 0-1 score indicating pattern confidence
        - avg_gap_days: average gap between occurrences
        - regularity_score: how consistent the gaps are (0-1)
    """
    if len(dates) < 2:
        return 'insufficient_data', 0.0, 0, 0.0

    # Sort dates
    dates = sorted(dates)

    # Calculate gaps between consecutive occurrences (in days)
    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]

    if len(gaps) == 0:
        return 'single_occurrence', 0.0, 0, 0.0

    avg_gap = np.mean(gaps)
    std_gap = np.std(gaps)

    # Calculate coefficient of variation for gaps (lower = more regular)
    cv_gap = std_gap / avg_gap if avg_gap > 0 else 1.0

    # Regularity score (1.0 = perfectly regular, 0.0 = very irregular)
    # If CV < 0.2, very regular; CV > 1.0, very irregular
    regularity_score = max(0, 1 - min(cv_gap, 1.0))

    # Determine frequency based on average gap
    # Daily: ~7 days (weekly data, but appears every week)
    # Weekly: ~7 days with high regularity
    # Biweekly: ~14 days
    # Monthly: ~30 days (allowing for 28-31 day months)
    # Quarterly: ~90 days (allowing for 84-98 days)
    # Semi-annual: ~180 days

    if avg_gap <= 10 and regularity_score > 0.5:
        # Appears almost every week
        frequency = 'daily'
        confidence = regularity_score
    elif 10 < avg_gap <= 21 and regularity_score > 0.4:
        # Appears every 2-3 weeks
        frequency = 'weekly'
        confidence = regularity_score
    elif 21 < avg_gap <= 45:
        # Appears roughly monthly
        if regularity_score > 0.4:
            frequency = 'biweekly'
        else:
            frequency = 'monthly'
        confidence = regularity_score
    elif 45 < avg_gap <= 120:
        # Appears quarterly-ish
        frequency = 'monthly' if regularity_score > 0.5 else 'quarterly'
        confidence = regularity_score * 0.8
    elif 120 < avg_gap <= 270:
        # Appears semi-annually
        frequency = 'quarterly' if regularity_score > 0.5 else 'semi_annual'
        confidence = regularity_score * 0.7
    else:
        # Very infrequent or irregular
        frequency = 'semi_annual' if regularity_score > 0.3 else 'irregular'
        confidence = regularity_score * 0.5

    # Additional check: if gaps are very inconsistent, mark as irregular
    if regularity_score < 0.3 and len(gaps) > 3:
        frequency = 'irregular'
        confidence = 1 - regularity_score  # Higher confidence in irregularity

    return frequency, confidence, avg_gap, regularity_score


def detect_frequency_advanced(group_df, total_weeks=104):
    """
    Advanced frequency detection using pattern analysis

    Args:
        group_df: DataFrame with volume data for specific app-message combination
        total_weeks: Total weeks in the analysis period

    Returns:
        dict with frequency analysis results
    """
    dates = group_df['week_start_date'].tolist()
    weeks_with_data = len(dates)
    occurrence_rate = weeks_with_data / total_weeks

    # Analyze the pattern
    frequency, confidence, avg_gap, regularity = analyze_occurrence_pattern(dates)

    # Additional metrics
    volumes = group_df['volume'].values

    return {
        'frequency_category': frequency,
        'confidence': confidence,
        'weeks_with_data': weeks_with_data,
        'occurrence_rate': occurrence_rate,
        'avg_gap_days': avg_gap,
        'regularity_score': regularity,
        'avg_volume': np.mean(volumes),
        'std_volume': np.std(volumes),
        'min_volume': np.min(volumes),
        'max_volume': np.max(volumes),
        'cv_volume': np.std(volumes) / np.mean(volumes) if np.mean(volumes) > 0 else 0,
        'total_occurrences': len(dates)
    }


def get_frequency_summary(frequency_results):
    """
    Generate human-readable summary of frequency analysis
    """
    freq = frequency_results['frequency_category']
    conf = frequency_results['confidence']
    gap = frequency_results['avg_gap_days']
    reg = frequency_results['regularity_score']

    confidence_text = "high" if conf > 0.7 else "medium" if conf > 0.4 else "low"
    regularity_text = "regular" if reg > 0.7 else "somewhat regular" if reg > 0.4 else "irregular"

    summary = f"{freq.upper()} pattern (confidence: {confidence_text}, {regularity_text})"
    summary += f" | Avg gap: {gap:.1f} days | {frequency_results['total_occurrences']} occurrences"

    return summary


if __name__ == "__main__":
    # Test with sample data
    import pandas as pd
    from datetime import datetime, timedelta

    print("Testing Frequency Detection...")
    print("="*80)

    # Test case 1: Regular weekly pattern
    start = datetime(2023, 1, 2)  # Monday
    weekly_dates = [start + timedelta(weeks=i) for i in range(52)]
    df_weekly = pd.DataFrame({'week_start_date': weekly_dates, 'volume': [1000]*52})

    result = detect_frequency_advanced(df_weekly)
    print("\nTest 1 - Regular Weekly Pattern:")
    print(get_frequency_summary(result))

    # Test case 2: Monthly pattern (every 4 weeks)
    monthly_dates = [start + timedelta(weeks=i*4) for i in range(13)]
    df_monthly = pd.DataFrame({'week_start_date': monthly_dates, 'volume': [5000]*13})

    result = detect_frequency_advanced(df_monthly)
    print("\nTest 2 - Monthly Pattern:")
    print(get_frequency_summary(result))

    # Test case 3: Irregular pattern
    irregular_dates = [start + timedelta(weeks=w) for w in [0, 2, 8, 10, 30, 45, 50]]
    df_irregular = pd.DataFrame({'week_start_date': irregular_dates, 'volume': [2000]*7})

    result = detect_frequency_advanced(df_irregular)
    print("\nTest 3 - Irregular Pattern:")
    print(get_frequency_summary(result))

    # Test case 4: Quarterly pattern
    quarterly_dates = [start + timedelta(weeks=i*13) for i in range(4)]
    df_quarterly = pd.DataFrame({'week_start_date': quarterly_dates, 'volume': [10000]*4})

    result = detect_frequency_advanced(df_quarterly)
    print("\nTest 4 - Quarterly Pattern:")
    print(get_frequency_summary(result))

    print("\n" + "="*80)
    print("Testing Complete!")
