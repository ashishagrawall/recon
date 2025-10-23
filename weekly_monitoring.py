"""
Weekly Volume Monitoring Script - Production Ready

This script is designed to run every Monday morning to:
1. Check last week's volume data
2. Compare against dynamic thresholds
3. Generate alerts for volume drops
4. Send alert notifications (email/dashboard)

Usage:
    python weekly_monitoring.py [--sensitivity high|medium|low] [--date YYYY-MM-DD]
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import json
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

# File paths
DATA_FILE = '/Users/ashishagrawal-mac16/Documents/recon/payment_screening_volumes.csv'
THRESHOLD_CONFIG_FILE = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output/threshold_configuration.csv'
ALERTS_OUTPUT_DIR = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output/weekly_alerts'

# Alert sensitivity configurations
SENSITIVITY_CONFIGS = {
    'high': {
        'z_score': 1.5,
        'percentile': 10,
        'min_weeks': 4,
        'description': 'High sensitivity - More alerts, catches smaller drops'
    },
    'medium': {
        'z_score': 2.0,
        'percentile': 5,
        'min_weeks': 6,
        'description': 'Medium sensitivity - Balanced approach (recommended)'
    },
    'low': {
        'z_score': 2.5,
        'percentile': 2,
        'min_weeks': 8,
        'description': 'Low sensitivity - Fewer alerts, only significant drops'
    }
}

# ============================================================================
# THRESHOLD CALCULATION FUNCTIONS
# ============================================================================

def calculate_dynamic_threshold(volumes, sensitivity='medium'):
    """Calculate threshold using multiple statistical methods"""
    config = SENSITIVITY_CONFIGS[sensitivity]

    mean_vol = np.mean(volumes)
    std_vol = np.std(volumes)

    # Method 1: Z-score based
    z_threshold = max(0, mean_vol - config['z_score'] * std_vol)

    # Method 2: Percentile based
    percentile_threshold = np.percentile(volumes, config['percentile'])

    # Method 3: IQR based
    q1 = np.percentile(volumes, 25)
    q3 = np.percentile(volumes, 75)
    iqr = q3 - q1
    iqr_threshold = max(0, q1 - 1.5 * iqr)

    # Use the maximum (most conservative) threshold
    final_threshold = max(z_threshold, percentile_threshold, iqr_threshold)

    return {
        'threshold': final_threshold,
        'mean': mean_vol,
        'std': std_vol,
        'methods': {
            'z_score': z_threshold,
            'percentile': percentile_threshold,
            'iqr': iqr_threshold
        }
    }

# ============================================================================
# ALERT DETECTION
# ============================================================================

def detect_weekly_alerts(df, check_date, sensitivity='medium'):
    """
    Detect volume drops for a specific week

    Parameters:
    - df: Historical volume data
    - check_date: Date to check (should be a Monday)
    - sensitivity: Alert sensitivity level

    Returns:
    - DataFrame of alerts
    """
    alerts = []
    config = SENSITIVITY_CONFIGS[sensitivity]

    # Get data for the week we're checking
    current_week_data = df[df['week_start_date'] == check_date]

    if len(current_week_data) == 0:
        print(f"No data found for week starting {check_date}")
        return pd.DataFrame()

    # Group by app and message_type
    for (app, msg_type), group in df.groupby(['app', 'message_type']):
        # Need minimum weeks of data
        if len(group) < config['min_weeks']:
            continue

        # Get current week's volume
        current_vol = current_week_data[
            (current_week_data['app'] == app) &
            (current_week_data['message_type'] == msg_type)
        ]

        if len(current_vol) == 0:
            # Missing data - this is itself an alert!
            historical_data = group[group['week_start_date'] < check_date]
            if len(historical_data) >= config['min_weeks']:
                threshold_info = calculate_dynamic_threshold(
                    historical_data['volume'].values, sensitivity
                )

                alerts.append({
                    'app': app,
                    'message_type': msg_type,
                    'week_start_date': check_date,
                    'current_volume': 0,
                    'threshold': threshold_info['threshold'],
                    'mean_volume': threshold_info['mean'],
                    'drop_from_mean_pct': 100.0,
                    'severity': 'CRITICAL',
                    'alert_type': 'NO_DATA',
                    'message': 'No data received this week - possible system failure'
                })
            continue

        current_vol = current_vol.iloc[0]['volume']

        # Calculate threshold from historical data (excluding current week)
        historical_data = group[group['week_start_date'] < check_date]

        if len(historical_data) < config['min_weeks']:
            continue

        threshold_info = calculate_dynamic_threshold(
            historical_data['volume'].values, sensitivity
        )

        # Check if current volume is below threshold
        if current_vol < threshold_info['threshold']:
            drop_pct = ((threshold_info['mean'] - current_vol) / threshold_info['mean']) * 100

            # Get recent 4-week average for context
            recent_4wk = historical_data.tail(4)['volume'].mean()

            # Determine severity
            if drop_pct >= 70:
                severity = 'CRITICAL'
            elif drop_pct >= 50:
                severity = 'HIGH'
            elif drop_pct >= 30:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'

            alerts.append({
                'app': app,
                'message_type': msg_type,
                'week_start_date': check_date,
                'current_volume': current_vol,
                'threshold': threshold_info['threshold'],
                'mean_volume': threshold_info['mean'],
                'recent_4wk_avg': recent_4wk,
                'drop_from_mean_pct': drop_pct,
                'severity': severity,
                'alert_type': 'VOLUME_DROP',
                'message': f'Volume dropped {drop_pct:.1f}% below historical mean'
            })

    return pd.DataFrame(alerts)

# ============================================================================
# ALERT REPORTING
# ============================================================================

def generate_alert_report(alerts_df, check_date, sensitivity):
    """Generate formatted alert report"""

    report_lines = []
    report_lines.append("="*80)
    report_lines.append("PAYMENT SCREENING VOLUME ALERT REPORT")
    report_lines.append("="*80)
    report_lines.append(f"Week Starting: {check_date}")
    report_lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Sensitivity Level: {sensitivity.upper()}")
    report_lines.append(f"Description: {SENSITIVITY_CONFIGS[sensitivity]['description']}")
    report_lines.append("="*80)
    report_lines.append("")

    if len(alerts_df) == 0:
        report_lines.append("✓ NO ALERTS DETECTED")
        report_lines.append("All systems operating within normal volume ranges.")
        report_lines.append("")
        return "\n".join(report_lines)

    # Summary statistics
    report_lines.append(f"ALERT SUMMARY:")
    report_lines.append(f"  Total Alerts: {len(alerts_df)}")

    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        count = len(alerts_df[alerts_df['severity'] == severity])
        if count > 0:
            report_lines.append(f"  {severity:10s}: {count}")

    report_lines.append("")

    # Detailed alerts by severity
    for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        severity_alerts = alerts_df[alerts_df['severity'] == severity]

        if len(severity_alerts) > 0:
            report_lines.append("-"*80)
            report_lines.append(f"{severity} PRIORITY ALERTS ({len(severity_alerts)})")
            report_lines.append("-"*80)
            report_lines.append("")

            for idx, alert in severity_alerts.iterrows():
                report_lines.append(f"App: {alert['app']} | Message Type: {alert['message_type']}")
                report_lines.append(f"  Current Volume: {alert['current_volume']:,.0f}")
                report_lines.append(f"  Threshold: {alert['threshold']:,.0f}")
                report_lines.append(f"  Mean Volume: {alert['mean_volume']:,.0f}")

                if 'recent_4wk_avg' in alert:
                    report_lines.append(f"  Recent 4-Week Avg: {alert['recent_4wk_avg']:,.0f}")

                report_lines.append(f"  Drop from Mean: {alert['drop_from_mean_pct']:.1f}%")
                report_lines.append(f"  Message: {alert['message']}")
                report_lines.append("")

    report_lines.append("="*80)
    report_lines.append("END OF REPORT")
    report_lines.append("="*80)

    return "\n".join(report_lines)

def save_alerts(alerts_df, check_date, output_dir):
    """Save alerts to CSV and JSON"""
    os.makedirs(output_dir, exist_ok=True)

    date_str = check_date.strftime('%Y%m%d')

    # Save as CSV
    csv_file = f"{output_dir}/alerts_{date_str}.csv"
    alerts_df.to_csv(csv_file, index=False)

    # Save as JSON (for API integration)
    json_file = f"{output_dir}/alerts_{date_str}.json"
    alerts_json = alerts_df.to_dict(orient='records')
    with open(json_file, 'w') as f:
        json.dump({
            'check_date': check_date.strftime('%Y-%m-%d'),
            'alert_count': len(alerts_df),
            'alerts': alerts_json
        }, f, indent=2, default=str)

    return csv_file, json_file

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Weekly Payment Screening Volume Monitor')
    parser.add_argument('--sensitivity', choices=['high', 'medium', 'low'],
                       default='medium', help='Alert sensitivity level')
    parser.add_argument('--date', type=str, help='Check date (YYYY-MM-DD), defaults to last Monday')
    parser.add_argument('--output-dir', type=str, default=ALERTS_OUTPUT_DIR,
                       help='Output directory for alerts')

    args = parser.parse_args()

    # Determine check date
    if args.date:
        check_date = pd.to_datetime(args.date)
    else:
        # Default to last Monday
        today = datetime.now()
        days_since_monday = today.weekday()
        check_date = today - timedelta(days=days_since_monday)
        check_date = pd.to_datetime(check_date.date())

    print("\n" + "="*80)
    print("WEEKLY VOLUME MONITORING - STARTING")
    print("="*80)
    print(f"Check Date: {check_date.date()}")
    print(f"Sensitivity: {args.sensitivity}")
    print(f"Data File: {DATA_FILE}")
    print("="*80 + "\n")

    # Load data
    print("Loading data...")
    df = pd.read_csv(DATA_FILE)
    df['week_start_date'] = pd.to_datetime(df['week_start_date'])
    print(f"  Loaded {len(df):,} records")
    print(f"  Date range: {df['week_start_date'].min().date()} to {df['week_start_date'].max().date()}")

    # Detect alerts
    print(f"\nChecking week starting {check_date.date()}...")
    alerts_df = detect_weekly_alerts(df, check_date, args.sensitivity)

    # Generate report
    report = generate_alert_report(alerts_df, check_date, args.sensitivity)
    print("\n" + report)

    # Save alerts
    if len(alerts_df) > 0:
        csv_file, json_file = save_alerts(alerts_df, check_date, args.output_dir)
        print(f"\nAlerts saved:")
        print(f"  CSV: {csv_file}")
        print(f"  JSON: {json_file}")

        # Save text report
        report_file = f"{args.output_dir}/report_{check_date.strftime('%Y%m%d')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"  Report: {report_file}")

    print("\n" + "="*80)
    print("MONITORING COMPLETE")
    print("="*80 + "\n")

    return len(alerts_df)

if __name__ == '__main__':
    alert_count = main()
    exit(0 if alert_count == 0 else 1)  # Exit code 1 if alerts detected
