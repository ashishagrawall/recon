"""
Comprehensive Trend Analysis Module

Analyzes volume trends across multiple time windows:
2 weeks, 1 month, 3 months, 6 months, 9 months, 12 months, 18 months
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats


def calculate_trend_metrics(volumes, dates):
    """
    Calculate trend metrics for a given period

    Returns:
        - avg_volume: Average volume
        - trend_direction: increasing/decreasing/stable
        - growth_rate: Percentage growth rate
        - volatility: Standard deviation / mean
        - slope: Linear regression slope
    """
    if len(volumes) == 0:
        return {
            'avg_volume': 0,
            'total_volume': 0,
            'trend_direction': 'no_data',
            'growth_rate_pct': 0,
            'volatility': 0,
            'slope': 0,
            'data_points': 0
        }

    avg_volume = np.mean(volumes)
    total_volume = np.sum(volumes)
    volatility = np.std(volumes) / avg_volume if avg_volume > 0 else 0

    # Calculate linear regression to determine trend
    if len(volumes) >= 2:
        x = np.arange(len(volumes))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, volumes)

        # Calculate growth rate (first vs last)
        first_half_avg = np.mean(volumes[:len(volumes)//2]) if len(volumes) >= 4 else volumes[0]
        second_half_avg = np.mean(volumes[len(volumes)//2:]) if len(volumes) >= 4 else volumes[-1]

        if first_half_avg > 0:
            growth_rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        else:
            growth_rate = 0

        # Determine trend direction based on slope and growth rate
        if abs(growth_rate) < 5:  # Less than 5% change
            trend_direction = 'stable'
        elif growth_rate > 5:
            trend_direction = 'increasing'
        else:
            trend_direction = 'decreasing'
    else:
        slope = 0
        growth_rate = 0
        trend_direction = 'insufficient_data'

    return {
        'avg_volume': avg_volume,
        'total_volume': total_volume,
        'trend_direction': trend_direction,
        'growth_rate_pct': growth_rate,
        'volatility': volatility,
        'slope': slope,
        'data_points': len(volumes),
        'min_volume': np.min(volumes),
        'max_volume': np.max(volumes),
        'median_volume': np.median(volumes)
    }


def analyze_trends_multi_window(group_df, reference_date=None):
    """
    Analyze trends across multiple time windows

    Windows: 2 weeks, 1 month, 3 months, 6 months, 9 months, 12 months, 18 months

    Args:
        group_df: DataFrame with week_start_date and volume columns
        reference_date: Date to analyze from (default: latest date in data)

    Returns:
        Dictionary with trend analysis for each window
    """
    if reference_date is None:
        reference_date = group_df['week_start_date'].max()

    # Define time windows (in weeks)
    windows = {
        '2_weeks': 2,
        '1_month': 4,
        '3_months': 13,
        '6_months': 26,
        '9_months': 39,
        '12_months': 52,
        '18_months': 78
    }

    results = {}

    for window_name, weeks_back in windows.items():
        # Calculate cutoff date
        cutoff_date = reference_date - timedelta(weeks=weeks_back)

        # Filter data for this window
        window_data = group_df[
            (group_df['week_start_date'] > cutoff_date) &
            (group_df['week_start_date'] <= reference_date)
        ].sort_values('week_start_date')

        # Calculate metrics
        volumes = window_data['volume'].values
        dates = window_data['week_start_date'].values

        results[window_name] = calculate_trend_metrics(volumes, dates)

    return results


def compare_recent_to_historical(group_df, recent_weeks=4):
    """
    Compare recent performance (last N weeks) to historical average

    Args:
        group_df: DataFrame with volume data
        recent_weeks: Number of recent weeks to compare

    Returns:
        Comparison metrics
    """
    if len(group_df) < recent_weeks + 4:
        return {
            'recent_avg': 0,
            'historical_avg': 0,
            'change_pct': 0,
            'status': 'insufficient_data'
        }

    # Sort by date
    df_sorted = group_df.sort_values('week_start_date')

    # Recent data
    recent_data = df_sorted.tail(recent_weeks)
    recent_avg = recent_data['volume'].mean()

    # Historical data (everything before recent)
    historical_data = df_sorted.iloc[:-recent_weeks]
    historical_avg = historical_data['volume'].mean()

    # Calculate change
    if historical_avg > 0:
        change_pct = ((recent_avg - historical_avg) / historical_avg) * 100
    else:
        change_pct = 0

    # Determine status
    if abs(change_pct) < 10:
        status = 'normal'
    elif change_pct > 10:
        status = 'increasing'
    elif change_pct < -10:
        status = 'decreasing'
    else:
        status = 'normal'

    return {
        'recent_avg': recent_avg,
        'historical_avg': historical_avg,
        'change_pct': change_pct,
        'status': status,
        'recent_weeks': recent_weeks
    }


def get_trend_summary(trend_results):
    """
    Generate human-readable summary of trend analysis
    """
    summary_lines = []

    for window, metrics in trend_results.items():
        if metrics['data_points'] == 0:
            summary_lines.append(f"{window}: No data")
            continue

        direction_symbol = {
            'increasing': '↗',
            'decreasing': '↘',
            'stable': '→',
            'insufficient_data': '?',
            'no_data': '-'
        }.get(metrics['trend_direction'], '?')

        summary = f"{window:12s}: {direction_symbol} {metrics['trend_direction']:12s} | "
        summary += f"Avg: {metrics['avg_volume']:>12,.0f} | "
        summary += f"Growth: {metrics['growth_rate_pct']:>6.1f}% | "
        summary += f"Vol: {metrics['volatility']:.2f} | "
        summary += f"Points: {metrics['data_points']}"

        summary_lines.append(summary)

    return "\n".join(summary_lines)


if __name__ == "__main__":
    # Test with sample data
    print("Testing Trend Analysis...")
    print("="*80)

    # Create sample data with increasing trend
    from datetime import datetime, timedelta

    start_date = datetime(2023, 1, 2)
    dates = [start_date + timedelta(weeks=i) for i in range(52)]

    # Increasing trend with some noise
    base_volume = 1000000
    volumes = [base_volume * (1 + i*0.02) + np.random.normal(0, base_volume*0.1)
               for i in range(52)]

    df_test = pd.DataFrame({
        'week_start_date': dates,
        'volume': volumes
    })

    # Analyze trends
    trends = analyze_trends_multi_window(df_test)

    print("\nTrend Analysis Across Time Windows:")
    print("-"*80)
    print(get_trend_summary(trends))

    # Compare recent to historical
    comparison = compare_recent_to_historical(df_test, recent_weeks=4)

    print("\n" + "-"*80)
    print("\nRecent vs Historical Comparison:")
    print(f"  Recent 4 weeks avg:    {comparison['recent_avg']:>15,.0f}")
    print(f"  Historical avg:        {comparison['historical_avg']:>15,.0f}")
    print(f"  Change:                {comparison['change_pct']:>15.1f}%")
    print(f"  Status:                {comparison['status']:>15s}")

    print("\n" + "="*80)
    print("Testing Complete!")
