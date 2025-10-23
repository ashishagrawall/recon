"""
Payment Screening Volume Analysis V2 - Enhanced Version

Improvements:
1. Better frequency detection based on actual spacing/regularity
2. Comprehensive trend analysis (2W, 1M, 3M, 6M, 9M, 12M, 18M)
3. Pattern-based threshold calculation
4. Enhanced alerting

This version uses the new frequency_detector and trend_analyzer modules.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import our custom modules
from frequency_detector import detect_frequency_advanced, get_frequency_summary
from trend_analyzer import analyze_trends_multi_window, compare_recent_to_historical, get_trend_summary

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_FILE = '/Users/ashishagrawal-mac16/Documents/recon/payment_screening_volumes.csv'
OUTPUT_DIR = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output_v2'

# Alert sensitivity levels
SENSITIVITY_LEVELS = {
    'high': {'z_score': 1.5, 'percentile': 10, 'min_weeks': 4},
    'medium': {'z_score': 2.0, 'percentile': 5, 'min_weeks': 6},
    'low': {'z_score': 2.5, 'percentile': 2, 'min_weeks': 8}
}

CURRENT_SENSITIVITY = 'medium'

# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def main():
    print("="*80)
    print("PAYMENT SCREENING VOLUME ANALYSIS V2 - ENHANCED")
    print("="*80)
    print(f"\nLoading data from: {DATA_FILE}")

    # Load data
    df = pd.read_csv(DATA_FILE)
    df['week_start_date'] = pd.to_datetime(df['week_start_date'])
    df = df.sort_values(['app', 'message_type', 'week_start_date']).reset_index(drop=True)

    print(f"\nDataset Summary:")
    print(f"  Total records: {len(df):,}")
    print(f"  Date range: {df['week_start_date'].min().date()} to {df['week_start_date'].max().date()}")
    print(f"  Number of apps: {df['app'].nunique()}")
    print(f"  Number of message types: {df['message_type'].nunique()}")
    print(f"  Unique app-message combinations: {df.groupby(['app', 'message_type']).ngroups:,}")
    print(f"  Total volume: {df['volume'].sum():,}")

    # ============================================================================
    # ENHANCED FREQUENCY DETECTION
    # ============================================================================

    print("\n" + "="*80)
    print("STEP 1: ADVANCED FREQUENCY PATTERN DETECTION")
    print("="*80)
    print("\nAnalyzing actual spacing and regularity of message occurrences...")

    frequency_results = []

    for (app, msg_type), group in df.groupby(['app', 'message_type']):
        freq_analysis = detect_frequency_advanced(group)

        frequency_results.append({
            'app': app,
            'message_type': msg_type,
            **freq_analysis
        })

    freq_df = pd.DataFrame(frequency_results)

    # Display frequency distribution
    print("\nFrequency Distribution (Pattern-Based):")
    freq_counts = freq_df['frequency_category'].value_counts().sort_index()
    for freq, count in freq_counts.items():
        pct = (count / len(freq_df)) * 100
        avg_vol = freq_df[freq_df['frequency_category'] == freq]['avg_volume'].mean()
        avg_conf = freq_df[freq_df['frequency_category'] == freq]['confidence'].mean()
        avg_reg = freq_df[freq_df['frequency_category'] == freq]['regularity_score'].mean()

        print(f"  {freq:15s}: {count:4d} combinations ({pct:5.1f}%)")
        print(f"    └─ Avg Volume: {avg_vol:>12,.0f} | Confidence: {avg_conf:.2f} | Regularity: {avg_reg:.2f}")

    # Show examples
    print("\nExample Patterns (Top 5 by volume):")
    print("-"*80)
    top_5 = freq_df.nlargest(5, 'avg_volume')
    for idx, row in top_5.iterrows():
        print(f"\n{row['app']} - {row['message_type']}:")
        print(f"  Pattern: {row['frequency_category'].upper()}")
        print(f"  Confidence: {row['confidence']:.2f} | Regularity: {row['regularity_score']:.2f}")
        print(f"  Avg Gap: {row['avg_gap_days']:.1f} days | Occurrences: {row['total_occurrences']}")
        print(f"  Avg Volume: {row['avg_volume']:,.0f}")

    # ============================================================================
    # TREND ANALYSIS
    # ============================================================================

    print("\n" + "="*80)
    print("STEP 2: MULTI-WINDOW TREND ANALYSIS")
    print("="*80)
    print("\nAnalyzing trends across 2W, 1M, 3M, 6M, 9M, 12M, 18M windows...")

    trend_results = []

    # Analyze trends for top 10 combinations by volume
    top_combinations = freq_df.nlargest(10, 'avg_volume')[['app', 'message_type']]

    for idx, row in top_combinations.iterrows():
        app, msg_type = row['app'], row['message_type']
        group_data = df[(df['app'] == app) & (df['message_type'] == msg_type)]

        trends = analyze_trends_multi_window(group_data)
        comparison = compare_recent_to_historical(group_data, recent_weeks=4)

        trend_results.append({
            'app': app,
            'message_type': msg_type,
            'trends': trends,
            'recent_vs_historical': comparison
        })

    # Display trend analysis for top 3
    print("\nTrend Analysis (Top 3 by Volume):")
    print("="*80)

    for i, result in enumerate(trend_results[:3]):
        print(f"\n[{i+1}] {result['app']} - {result['message_type']}")
        print("-"*80)
        print(get_trend_summary(result['trends']))

        comp = result['recent_vs_historical']
        print(f"\nRecent (4W) vs Historical:")
        print(f"  Recent Avg:     {comp['recent_avg']:>15,.0f}")
        print(f"  Historical Avg: {comp['historical_avg']:>15,.0f}")
        print(f"  Change:         {comp['change_pct']:>14.1f}%  ({comp['status']})")

    # ============================================================================
    # DYNAMIC THRESHOLD CALCULATION (Pattern-Aware)
    # ============================================================================

    print("\n" + "="*80)
    print(f"STEP 3: PATTERN-AWARE THRESHOLD CALCULATION")
    print(f"Sensitivity: {CURRENT_SENSITIVITY.upper()}")
    print("="*80)

    threshold_data = []
    config = SENSITIVITY_LEVELS[CURRENT_SENSITIVITY]

    for idx, row in freq_df.iterrows():
        app, msg_type = row['app'], row['message_type']
        group = df[(df['app'] == app) & (df['message_type'] == msg_type)]

        if len(group) < config['min_weeks']:
            continue

        volumes = group['volume'].values
        mean_vol = np.mean(volumes)
        std_vol = np.std(volumes)

        # Adjust threshold based on pattern regularity
        # More irregular patterns get more lenient thresholds
        regularity_factor = row['regularity_score']  # 0-1
        adjusted_z = config['z_score'] * (1 + (1 - regularity_factor) * 0.5)

        # Calculate thresholds
        z_threshold = max(0, mean_vol - adjusted_z * std_vol)
        percentile_threshold = np.percentile(volumes, config['percentile'])

        q1 = np.percentile(volumes, 25)
        q3 = np.percentile(volumes, 75)
        iqr = q3 - q1
        iqr_threshold = max(0, q1 - 1.5 * iqr)

        final_threshold = max(z_threshold, percentile_threshold, iqr_threshold)

        threshold_data.append({
            'app': app,
            'message_type': msg_type,
            'frequency_category': row['frequency_category'],
            'regularity_score': row['regularity_score'],
            'mean_volume': mean_vol,
            'std_volume': std_vol,
            'threshold': final_threshold,
            'adjusted_z_score': adjusted_z,
            'z_threshold': z_threshold,
            'percentile_threshold': percentile_threshold,
            'iqr_threshold': iqr_threshold
        })

    threshold_df = pd.DataFrame(threshold_data)

    print(f"\nThresholds calculated for {len(threshold_df)} combinations")
    print(f"(Minimum {config['min_weeks']} weeks of data required)")

    # Show examples by frequency category
    print("\nExample Thresholds by Pattern:")
    print("-"*80)
    for freq_cat in ['daily', 'weekly', 'monthly', 'irregular']:
        sample = threshold_df[threshold_df['frequency_category'] == freq_cat]
        if len(sample) > 0:
            example = sample.iloc[0]
            print(f"\n{freq_cat.upper()}:")
            print(f"  {example['app']} - {example['message_type']}")
            print(f"  Mean: {example['mean_volume']:>12,.0f} | Threshold: {example['threshold']:>12,.0f}")
            print(f"  Regularity: {example['regularity_score']:.2f} | Adjusted Z: {example['adjusted_z_score']:.2f}")

    # ============================================================================
    # SAVE RESULTS
    # ============================================================================

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Save frequency analysis
    freq_file = f'{OUTPUT_DIR}/frequency_analysis.csv'
    freq_df.to_csv(freq_file, index=False)
    print(f"\nFrequency analysis saved: {freq_file}")

    # Save threshold configuration
    threshold_file = f'{OUTPUT_DIR}/threshold_configuration.csv'
    threshold_df.to_csv(threshold_file, index=False)
    print(f"Threshold configuration saved: {threshold_file}")

    # Save trend analysis for top combinations
    trend_summary = []
    for result in trend_results:
        for window, metrics in result['trends'].items():
            trend_summary.append({
                'app': result['app'],
                'message_type': result['message_type'],
                'window': window,
                **metrics
            })

    trend_file = f'{OUTPUT_DIR}/trend_analysis.csv'
    pd.DataFrame(trend_summary).to_csv(trend_file, index=False)
    print(f"Trend analysis saved: {trend_file}")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\nOutputs saved to: {OUTPUT_DIR}/")
    print("\nNext steps:")
    print("  1. Review enhanced frequency patterns")
    print("  2. Analyze trend reports for key message types")
    print("  3. Use interactive_dashboard.py to explore specific patterns")
    print("  4. Run weekly_monitoring_v2.py for production monitoring")

if __name__ == "__main__":
    main()
