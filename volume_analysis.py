"""
Payment Screening Volume Analysis & Alerting System

This script analyzes historical volume data and implements dynamic threshold-based alerting
for payment screening systems with variable message frequencies.

Key Features:
1. Automatic frequency detection (daily, weekly, monthly, quarterly, semi-annual)
2. Dynamic threshold calculation using statistical methods
3. Anomaly detection with configurable sensitivity
4. Comprehensive visualizations for presentations
5. Alert generation for volume drops
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style for professional visualizations
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_FILE = '/Users/ashishagrawal-mac16/Documents/recon/payment_screening_volumes.csv'
OUTPUT_DIR = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output'

# Alert sensitivity levels
SENSITIVITY_LEVELS = {
    'high': {'z_score': 1.5, 'percentile': 10, 'min_weeks': 4},
    'medium': {'z_score': 2.0, 'percentile': 5, 'min_weeks': 6},
    'low': {'z_score': 2.5, 'percentile': 2, 'min_weeks': 8}
}

CURRENT_SENSITIVITY = 'medium'  # Change this to adjust alert sensitivity

# ============================================================================
# DATA LOADING & PREPARATION
# ============================================================================

print("="*80)
print("PAYMENT SCREENING VOLUME ANALYSIS & ALERTING SYSTEM")
print("="*80)
print(f"\nLoading data from: {DATA_FILE}")

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
# FREQUENCY DETECTION
# ============================================================================

def detect_frequency(group_df, total_weeks=104):
    """
    Automatically detect the frequency pattern of a message type

    Returns: frequency category and reliability score
    """
    weeks_with_data = len(group_df)
    occurrence_rate = weeks_with_data / total_weeks

    if occurrence_rate >= 0.95:
        return 'daily', occurrence_rate
    elif occurrence_rate >= 0.75:
        return 'weekly', occurrence_rate
    elif occurrence_rate >= 0.35:
        return 'biweekly', occurrence_rate
    elif occurrence_rate >= 0.15:
        return 'monthly', occurrence_rate
    elif occurrence_rate >= 0.05:
        return 'quarterly', occurrence_rate
    else:
        return 'semi_annual', occurrence_rate

print("\n" + "="*80)
print("ANALYZING MESSAGE FREQUENCIES")
print("="*80)

# Calculate frequency for each app-message combination
frequency_analysis = []

for (app, msg_type), group in df.groupby(['app', 'message_type']):
    freq_category, reliability = detect_frequency(group)

    frequency_analysis.append({
        'app': app,
        'message_type': msg_type,
        'frequency_category': freq_category,
        'weeks_with_data': len(group),
        'occurrence_rate': reliability,
        'avg_volume': group['volume'].mean(),
        'std_volume': group['volume'].std(),
        'min_volume': group['volume'].min(),
        'max_volume': group['volume'].max(),
        'cv': group['volume'].std() / group['volume'].mean() if group['volume'].mean() > 0 else 0  # Coefficient of variation
    })

freq_df = pd.DataFrame(frequency_analysis)

# Display frequency distribution
print("\nFrequency Distribution:")
freq_counts = freq_df['frequency_category'].value_counts().sort_index()
for freq, count in freq_counts.items():
    pct = (count / len(freq_df)) * 100
    avg_vol = freq_df[freq_df['frequency_category'] == freq]['avg_volume'].mean()
    print(f"  {freq:15s}: {count:4d} combinations ({pct:5.1f}%) - Avg Volume: {avg_vol:,.0f}")

# ============================================================================
# DYNAMIC THRESHOLD CALCULATION
# ============================================================================

def calculate_thresholds(group_df, sensitivity='medium'):
    """
    Calculate dynamic thresholds based on statistical methods

    Methods used:
    1. Z-score based (mean ± z*std)
    2. Percentile based (bottom X percentile)
    3. IQR based (Q1 - 1.5*IQR)
    4. Rolling average based
    """
    config = SENSITIVITY_LEVELS[sensitivity]

    volumes = group_df['volume'].values
    mean_vol = np.mean(volumes)
    std_vol = np.std(volumes)

    # Method 1: Z-score based threshold
    z_threshold = max(0, mean_vol - config['z_score'] * std_vol)

    # Method 2: Percentile based threshold
    percentile_threshold = np.percentile(volumes, config['percentile'])

    # Method 3: IQR based threshold
    q1 = np.percentile(volumes, 25)
    q3 = np.percentile(volumes, 75)
    iqr = q3 - q1
    iqr_threshold = max(0, q1 - 1.5 * iqr)

    # Method 4: Percentage drop from mean
    percentage_threshold = mean_vol * 0.7  # 30% drop from mean

    # Use the most conservative (highest) threshold
    final_threshold = max(z_threshold, percentile_threshold, iqr_threshold)

    return {
        'mean': mean_vol,
        'std': std_vol,
        'z_score_threshold': z_threshold,
        'percentile_threshold': percentile_threshold,
        'iqr_threshold': iqr_threshold,
        'percentage_threshold': percentage_threshold,
        'final_threshold': final_threshold,
        'cv': std_vol / mean_vol if mean_vol > 0 else 0
    }

print("\n" + "="*80)
print(f"CALCULATING DYNAMIC THRESHOLDS (Sensitivity: {CURRENT_SENSITIVITY.upper()})")
print("="*80)

# Calculate thresholds for each app-message combination
threshold_data = []

for (app, msg_type), group in df.groupby(['app', 'message_type']):
    if len(group) >= SENSITIVITY_LEVELS[CURRENT_SENSITIVITY]['min_weeks']:
        thresholds = calculate_thresholds(group, CURRENT_SENSITIVITY)

        threshold_data.append({
            'app': app,
            'message_type': msg_type,
            'weeks_of_data': len(group),
            'mean_volume': thresholds['mean'],
            'std_volume': thresholds['std'],
            'cv': thresholds['cv'],
            'threshold': thresholds['final_threshold'],
            'z_score_method': thresholds['z_score_threshold'],
            'percentile_method': thresholds['percentile_threshold'],
            'iqr_method': thresholds['iqr_threshold']
        })

threshold_df = pd.DataFrame(threshold_data)

print(f"\nThresholds calculated for {len(threshold_df)} app-message combinations")
print(f"(Minimum {SENSITIVITY_LEVELS[CURRENT_SENSITIVITY]['min_weeks']} weeks of data required)")

# Merge with frequency data
analysis_df = freq_df.merge(threshold_df, on=['app', 'message_type'], how='left')

print("\nSample Thresholds (Top 10 by volume):")
sample_cols = ['app', 'message_type', 'frequency_category', 'avg_volume', 'threshold']
if 'cv' in analysis_df.columns:
    sample_cols.append('cv')
sample = analysis_df.nlargest(10, 'avg_volume')[sample_cols]
print(sample.to_string(index=False))

# ============================================================================
# ALERT DETECTION (SIMULATING CURRENT WEEK CHECK)
# ============================================================================

def detect_alerts(df, threshold_df, current_week_date):
    """
    Detect volume drop alerts for the current week
    """
    alerts = []

    # Get current week data
    current_week_data = df[df['week_start_date'] == current_week_date]

    for _, row in current_week_data.iterrows():
        # Find threshold for this combination
        threshold_info = threshold_df[
            (threshold_df['app'] == row['app']) &
            (threshold_df['message_type'] == row['message_type'])
        ]

        if len(threshold_info) > 0:
            threshold_info = threshold_info.iloc[0]
            threshold = threshold_info['threshold']
            mean_vol = threshold_info['mean_volume']

            if row['volume'] < threshold:
                # Calculate severity
                drop_pct = ((mean_vol - row['volume']) / mean_vol) * 100

                # Get recent trend
                recent_data = df[
                    (df['app'] == row['app']) &
                    (df['message_type'] == row['message_type']) &
                    (df['week_start_date'] < current_week_date)
                ].tail(4)

                recent_avg = recent_data['volume'].mean() if len(recent_data) > 0 else mean_vol

                alerts.append({
                    'app': row['app'],
                    'message_type': row['message_type'],
                    'week_start_date': row['week_start_date'],
                    'current_volume': row['volume'],
                    'threshold': threshold,
                    'mean_volume': mean_vol,
                    'recent_4wk_avg': recent_avg,
                    'drop_from_mean_pct': drop_pct,
                    'severity': 'HIGH' if drop_pct > 50 else 'MEDIUM' if drop_pct > 30 else 'LOW'
                })

    return pd.DataFrame(alerts)

print("\n" + "="*80)
print("ALERT DETECTION - SIMULATING CURRENT WEEK")
print("="*80)

# Simulate checking the most recent week
most_recent_week = df['week_start_date'].max()
print(f"\nChecking week starting: {most_recent_week.date()}")

alerts_df = detect_alerts(df, threshold_df, most_recent_week)

if len(alerts_df) > 0:
    print(f"\n{'!'*80}")
    print(f"  {len(alerts_df)} ALERTS DETECTED!")
    print(f"{'!'*80}")

    # Show alerts by severity
    for severity in ['HIGH', 'MEDIUM', 'LOW']:
        severity_alerts = alerts_df[alerts_df['severity'] == severity]
        if len(severity_alerts) > 0:
            print(f"\n{severity} Priority Alerts ({len(severity_alerts)}):")
            display_cols = ['app', 'message_type', 'current_volume', 'threshold', 'drop_from_mean_pct']
            print(severity_alerts[display_cols].head(10).to_string(index=False))
else:
    print("\nNo alerts detected for this week.")

# Save alerts to CSV
if len(alerts_df) > 0:
    alerts_file = f'{OUTPUT_DIR}/alerts_{most_recent_week.date()}.csv'
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    alerts_df.to_csv(alerts_file, index=False)
    print(f"\nAlerts saved to: {alerts_file}")

# Save threshold configuration
threshold_config_file = f'{OUTPUT_DIR}/threshold_configuration.csv'
analysis_df.to_csv(threshold_config_file, index=False)
print(f"Threshold configuration saved to: {threshold_config_file}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\nNext steps:")
print(f"  1. Review alerts in: {OUTPUT_DIR}/")
print(f"  2. Run visualization script for charts and graphs")
print(f"  3. Adjust sensitivity level if needed (current: {CURRENT_SENSITIVITY})")
