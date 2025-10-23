"""
Enhanced Visualization Suite V2

Creates comprehensive visualizations using the improved V2 analysis:
1. Pattern-based frequency distribution
2. Confidence and regularity metrics
3. Multi-window trend analysis
4. Enhanced threshold visualization
5. Comparison charts
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_FILE = '/Users/ashishagrawal-mac16/Documents/recon/payment_screening_volumes.csv'
FREQ_FILE = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output_v2/frequency_analysis.csv'
THRESHOLD_FILE = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output_v2/threshold_configuration.csv'
TREND_FILE = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output_v2/trend_analysis.csv'
OUTPUT_DIR = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output_v2'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")
sns.set_palette("Set2")

print("="*80)
print("CREATING V2 ENHANCED VISUALIZATIONS")
print("="*80)

# Load data
df = pd.read_csv(DATA_FILE)
df['week_start_date'] = pd.to_datetime(df['week_start_date'])
df = df.sort_values(['app', 'message_type', 'week_start_date'])

freq_df = pd.read_csv(FREQ_FILE)
threshold_df = pd.read_csv(THRESHOLD_FILE)
trend_df = pd.read_csv(TREND_FILE)

print(f"\nLoaded data:")
print(f"  Volume records: {len(df):,}")
print(f"  Frequency analysis: {len(freq_df):,} combinations")
print(f"  Thresholds: {len(threshold_df):,} combinations")
print(f"  Trend data: {len(trend_df):,} records")

# ============================================================================
# 1. ENHANCED FREQUENCY DISTRIBUTION WITH CONFIDENCE
# ============================================================================

print("\n[1/10] Creating enhanced frequency distribution with confidence...")

fig, axes = plt.subplots(2, 2, figsize=(20, 12))
fig.suptitle('Enhanced Pattern Analysis - V2', fontsize=20, fontweight='bold')

# Pattern distribution pie chart
ax = axes[0, 0]
pattern_counts = freq_df['frequency_category'].value_counts()
colors = sns.color_palette("Set3", len(pattern_counts))
wedges, texts, autotexts = ax.pie(pattern_counts.values, labels=pattern_counts.index,
                                    autopct='%1.1f%%', startangle=90, colors=colors)
ax.set_title('Message Pattern Distribution', fontsize=14, fontweight='bold')
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')

# Confidence by pattern
ax = axes[0, 1]
conf_by_pattern = freq_df.groupby('frequency_category')['confidence'].mean().sort_values(ascending=False)
bars = ax.barh(range(len(conf_by_pattern)), conf_by_pattern.values,
               color=sns.color_palette("rocket", len(conf_by_pattern)))
ax.set_yticks(range(len(conf_by_pattern)))
ax.set_yticklabels(conf_by_pattern.index, fontsize=10)
ax.set_title('Average Confidence by Pattern', fontsize=14, fontweight='bold')
ax.set_xlabel('Confidence Score (0-1)', fontsize=12)
ax.set_xlim(0, 1)
ax.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, (idx, val) in enumerate(conf_by_pattern.items()):
    ax.text(val + 0.02, i, f'{val:.2f}', va='center', fontsize=10, fontweight='bold')

# Regularity by pattern
ax = axes[1, 0]
reg_by_pattern = freq_df.groupby('frequency_category')['regularity_score'].mean().sort_values(ascending=False)
bars = ax.barh(range(len(reg_by_pattern)), reg_by_pattern.values,
               color=sns.color_palette("mako", len(reg_by_pattern)))
ax.set_yticks(range(len(reg_by_pattern)))
ax.set_yticklabels(reg_by_pattern.index, fontsize=10)
ax.set_title('Average Regularity Score by Pattern', fontsize=14, fontweight='bold')
ax.set_xlabel('Regularity Score (0-1, higher = more regular)', fontsize=12)
ax.set_xlim(0, 1)
ax.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, (idx, val) in enumerate(reg_by_pattern.items()):
    ax.text(val + 0.02, i, f'{val:.2f}', va='center', fontsize=10, fontweight='bold')

# Confidence vs Regularity scatter
ax = axes[1, 1]
scatter = ax.scatter(freq_df['confidence'], freq_df['regularity_score'],
                    s=freq_df['avg_volume']/1000, alpha=0.6,
                    c=freq_df['frequency_category'].astype('category').cat.codes,
                    cmap='tab10', edgecolors='black', linewidth=0.5)
ax.set_xlabel('Confidence Score', fontsize=12, fontweight='bold')
ax.set_ylabel('Regularity Score', fontsize=12, fontweight='bold')
ax.set_title('Confidence vs Regularity\n(bubble size = volume)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 1.1)
ax.set_ylim(0, 1.1)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/v2_01_pattern_analysis.png', dpi=300, bbox_inches='tight')
print(f"   Saved: v2_01_pattern_analysis.png")
plt.close()

# ============================================================================
# 2. MULTI-WINDOW TREND ANALYSIS
# ============================================================================

print("[2/10] Creating multi-window trend analysis...")

# Get top 6 combinations for trend visualization
top_combos = freq_df.nlargest(6, 'avg_volume')[['app', 'message_type']]

fig, axes = plt.subplots(3, 2, figsize=(20, 16))
fig.suptitle('Multi-Window Trend Analysis (Top 6 by Volume)', fontsize=20, fontweight='bold')

windows = ['2_weeks', '1_month', '3_months', '6_months', '9_months', '12_months', '18_months']
window_labels = ['2W', '1M', '3M', '6M', '9M', '12M', '18M']

for idx, (_, row) in enumerate(top_combos.iterrows()):
    ax = axes[idx // 2, idx % 2]

    # Get trend data for this combination
    combo_trends = trend_df[
        (trend_df['app'] == row['app']) &
        (trend_df['message_type'] == row['message_type'])
    ]

    # Extract metrics for each window
    avg_volumes = []
    growth_rates = []

    for window in windows:
        window_data = combo_trends[combo_trends['window'] == window]
        if len(window_data) > 0:
            avg_volumes.append(window_data.iloc[0]['avg_volume'])
            growth_rates.append(window_data.iloc[0]['growth_rate_pct'])
        else:
            avg_volumes.append(0)
            growth_rates.append(0)

    # Plot average volume bars
    ax2 = ax.twinx()
    bars = ax.bar(window_labels, avg_volumes, alpha=0.6, color='lightblue', edgecolor='navy', linewidth=2)
    ax.set_ylabel('Average Volume', fontsize=11, fontweight='bold', color='navy')
    ax.tick_params(axis='y', labelcolor='navy')

    # Plot growth rate line
    line = ax2.plot(window_labels, growth_rates, marker='o', linewidth=3,
                    markersize=8, color='red', label='Growth Rate')
    ax2.set_ylabel('Growth Rate (%)', fontsize=11, fontweight='bold', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    # Format
    ax.set_title(f'{row["app"]} - {row["message_type"]}', fontsize=12, fontweight='bold')
    ax.set_xlabel('Time Window', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')

    # Format y-axis for volume
    ax.yaxis.set_major_formatter(plt.FuncFormatter(
        lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K'
    ))

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/v2_02_multiwindow_trends.png', dpi=300, bbox_inches='tight')
print(f"   Saved: v2_02_multiwindow_trends.png")
plt.close()

# ============================================================================
# 3. PATTERN-AWARE THRESHOLD COMPARISON
# ============================================================================

print("[3/10] Creating pattern-aware threshold comparison...")

fig, axes = plt.subplots(2, 2, figsize=(20, 12))
fig.suptitle('Pattern-Aware Threshold Analysis', fontsize=20, fontweight='bold')

# Threshold as % of mean by pattern
ax = axes[0, 0]
threshold_df['threshold_pct'] = (threshold_df['threshold'] / threshold_df['mean_volume']) * 100
threshold_pct_by_pattern = threshold_df.groupby('frequency_category')['threshold_pct'].mean().sort_values()
bars = ax.barh(range(len(threshold_pct_by_pattern)), threshold_pct_by_pattern.values,
               color=sns.color_palette("viridis", len(threshold_pct_by_pattern)))
ax.set_yticks(range(len(threshold_pct_by_pattern)))
ax.set_yticklabels(threshold_pct_by_pattern.index, fontsize=10)
ax.set_title('Threshold as % of Mean by Pattern', fontsize=14, fontweight='bold')
ax.set_xlabel('Threshold (% of Mean)', fontsize=12)
ax.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, val in enumerate(threshold_pct_by_pattern.values):
    ax.text(val + 1, i, f'{val:.1f}%', va='center', fontsize=10)

# Adjusted Z-score by pattern
ax = axes[0, 1]
z_by_pattern = threshold_df.groupby('frequency_category')['adjusted_z_score'].mean().sort_values()
bars = ax.barh(range(len(z_by_pattern)), z_by_pattern.values,
               color=sns.color_palette("coolwarm", len(z_by_pattern)))
ax.set_yticks(range(len(z_by_pattern)))
ax.set_yticklabels(z_by_pattern.index, fontsize=10)
ax.set_title('Adjusted Z-Score by Pattern\n(Higher = More Lenient)', fontsize=14, fontweight='bold')
ax.set_xlabel('Adjusted Z-Score', fontsize=12)
ax.grid(True, alpha=0.3, axis='x')

# Add value labels
for i, val in enumerate(z_by_pattern.values):
    ax.text(val + 0.05, i, f'{val:.2f}', va='center', fontsize=10)

# Regularity vs Z-score adjustment
ax = axes[1, 0]
scatter = ax.scatter(threshold_df['regularity_score'], threshold_df['adjusted_z_score'],
                    alpha=0.5, s=50, c=threshold_df['frequency_category'].astype('category').cat.codes,
                    cmap='tab10', edgecolors='black', linewidth=0.5)
ax.set_xlabel('Regularity Score', fontsize=12, fontweight='bold')
ax.set_ylabel('Adjusted Z-Score', fontsize=12, fontweight='bold')
ax.set_title('Regularity vs Z-Score Adjustment\n(Lower regularity → Higher Z → More lenient)',
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# Mean volume by pattern
ax = axes[1, 1]
mean_vol_by_pattern = threshold_df.groupby('frequency_category')['mean_volume'].mean().sort_values(ascending=False)
bars = ax.barh(range(len(mean_vol_by_pattern)), mean_vol_by_pattern.values,
               color=sns.color_palette("plasma", len(mean_vol_by_pattern)))
ax.set_yticks(range(len(mean_vol_by_pattern)))
ax.set_yticklabels(mean_vol_by_pattern.index, fontsize=10)
ax.set_title('Average Volume by Pattern', fontsize=14, fontweight='bold')
ax.set_xlabel('Average Weekly Volume', fontsize=12)
ax.xaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K'
))
ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/v2_03_threshold_analysis.png', dpi=300, bbox_inches='tight')
print(f"   Saved: v2_03_threshold_analysis.png")
plt.close()

# ============================================================================
# 4. PATTERN EXAMPLES WITH TREND LINES
# ============================================================================

print("[4/10] Creating pattern examples with trend analysis...")

# Select examples from different patterns
examples = []
for pattern in ['daily', 'weekly', 'irregular', 'monthly']:
    sample = freq_df[freq_df['frequency_category'] == pattern]
    if len(sample) > 0:
        # Get one with medium volume (not too high, not too low)
        sample = sample.sort_values('avg_volume')
        idx = len(sample) // 2
        examples.append(sample.iloc[idx])

if len(examples) >= 4:
    fig, axes = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle('Pattern Examples with Volume Trends', fontsize=20, fontweight='bold')

    for idx, example in enumerate(examples[:4]):
        ax = axes[idx // 2, idx % 2]

        # Get time series data
        ts_data = df[
            (df['app'] == example['app']) &
            (df['message_type'] == example['message_type'])
        ].sort_values('week_start_date')

        # Plot volume
        ax.plot(ts_data['week_start_date'], ts_data['volume'],
                marker='o', linewidth=2, markersize=4, label='Actual Volume',
                color='#2E86AB', alpha=0.8)

        # Plot mean
        mean_vol = example['avg_volume']
        ax.axhline(y=mean_vol, color='green', linestyle='--',
                   linewidth=2, label=f'Mean: {mean_vol:,.0f}', alpha=0.7)

        # Get threshold if available
        threshold_info = threshold_df[
            (threshold_df['app'] == example['app']) &
            (threshold_df['message_type'] == example['message_type'])
        ]

        if len(threshold_info) > 0:
            threshold = threshold_info.iloc[0]['threshold']
            ax.axhline(y=threshold, color='red', linestyle='--',
                       linewidth=2, label=f'Threshold: {threshold:,.0f}', alpha=0.7)

            # Highlight points below threshold
            below = ts_data[ts_data['volume'] < threshold]
            if len(below) > 0:
                ax.scatter(below['week_start_date'], below['volume'],
                          color='red', s=100, zorder=5, marker='X',
                          label=f'Alerts ({len(below)})', edgecolors='darkred', linewidth=2)

        # Add 4-week moving average
        if len(ts_data) >= 4:
            ts_data['ma4'] = ts_data['volume'].rolling(window=4, min_periods=1).mean()
            ax.plot(ts_data['week_start_date'], ts_data['ma4'],
                    linewidth=2.5, label='4-Week MA', color='orange', alpha=0.7)

        # Title with pattern info
        title = f'{example["app"]} - {example["message_type"]}\n'
        title += f'{example["frequency_category"].upper()} '
        title += f'(Conf: {example["confidence"]:.2f}, Reg: {example["regularity_score"]:.2f})'
        ax.set_title(title, fontsize=11, fontweight='bold')

        ax.set_xlabel('Week Start Date', fontsize=10)
        ax.set_ylabel('Volume', fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K' if x >= 1e3 else f'{int(x)}'
        ))
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/v2_04_pattern_examples.png', dpi=300, bbox_inches='tight')
    print(f"   Saved: v2_04_pattern_examples.png")
    plt.close()

# ============================================================================
# 5. EXECUTIVE SUMMARY DASHBOARD V2
# ============================================================================

print("[5/10] Creating enhanced executive summary dashboard...")

fig = plt.figure(figsize=(20, 14))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

fig.suptitle('PAYMENT SCREENING SYSTEM - EXECUTIVE SUMMARY V2 (Enhanced)',
             fontsize=22, fontweight='bold')

# Key metrics
ax1 = fig.add_subplot(gs[0, :])
ax1.axis('off')
metrics_text = f"""
KEY METRICS (Enhanced V2 Analysis)

Data Period: {df['week_start_date'].min().date()} to {df['week_start_date'].max().date()}
Total Messages Processed: {df['volume'].sum():,.0f}
Average Weekly Volume: {df.groupby('week_start_date')['volume'].sum().mean():,.0f}

Pattern Detection:
  - DAILY patterns: {len(freq_df[freq_df['frequency_category']=='daily'])} combinations ({len(freq_df[freq_df['frequency_category']=='daily'])/len(freq_df)*100:.1f}%)
  - IRREGULAR patterns: {len(freq_df[freq_df['frequency_category']=='irregular'])} combinations ({len(freq_df[freq_df['frequency_category']=='irregular'])/len(freq_df)*100:.1f}%)
  - Average Confidence: {freq_df['confidence'].mean():.2f}
  - Average Regularity: {freq_df['regularity_score'].mean():.2f}

Analysis Improvements:
  ✓ Pattern-based frequency detection
  ✓ Multi-window trend analysis (2W to 18M)
  ✓ Confidence and regularity scores
  ✓ Adaptive thresholds based on pattern
"""
ax1.text(0.1, 0.5, metrics_text, fontsize=13, verticalalignment='center',
         family='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.6))

# Pattern distribution
ax2 = fig.add_subplot(gs[1, 0])
pattern_counts = freq_df['frequency_category'].value_counts().head(6)
colors = sns.color_palette("Set3", len(pattern_counts))
wedges, texts, autotexts = ax2.pie(pattern_counts.values, labels=pattern_counts.index,
                                     autopct='%1.1f%%', startangle=90, colors=colors)
ax2.set_title('Top 6 Pattern Distribution', fontsize=12, fontweight='bold')
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(9)

# Volume trend
ax3 = fig.add_subplot(gs[1, 1:])
weekly_totals = df.groupby('week_start_date')['volume'].sum()
ax3.plot(weekly_totals.index, weekly_totals.values, linewidth=2, color='#2E86AB')
ax3.fill_between(weekly_totals.index, weekly_totals.values, alpha=0.3, color='#2E86AB')
ax3.set_title('Total Weekly Volume Trend', fontsize=12, fontweight='bold')
ax3.set_xlabel('Date', fontsize=10)
ax3.set_ylabel('Volume', fontsize=10)
ax3.yaxis.set_major_formatter(plt.FuncFormatter(
    lambda x, p: f'{int(x/1e9)}B' if x >= 1e9 else f'{int(x/1e6)}M'
))
ax3.grid(True, alpha=0.3)

# Confidence by pattern
ax4 = fig.add_subplot(gs[2, 0])
conf_by_pattern = freq_df.groupby('frequency_category')['confidence'].mean().nlargest(6)
ax4.barh(range(len(conf_by_pattern)), conf_by_pattern.values,
         color=sns.color_palette("rocket", len(conf_by_pattern)))
ax4.set_yticks(range(len(conf_by_pattern)))
ax4.set_yticklabels(conf_by_pattern.index, fontsize=9)
ax4.set_title('Confidence by Pattern (Top 6)', fontsize=12, fontweight='bold')
ax4.set_xlabel('Confidence', fontsize=10)
ax4.set_xlim(0, 1)
ax4.grid(True, alpha=0.3, axis='x')

# Regularity by pattern
ax5 = fig.add_subplot(gs[2, 1])
reg_by_pattern = freq_df.groupby('frequency_category')['regularity_score'].mean().nlargest(6)
ax5.barh(range(len(reg_by_pattern)), reg_by_pattern.values,
         color=sns.color_palette("mako", len(reg_by_pattern)))
ax5.set_yticks(range(len(reg_by_pattern)))
ax5.set_yticklabels(reg_by_pattern.index, fontsize=9)
ax5.set_title('Regularity by Pattern (Top 6)', fontsize=12, fontweight='bold')
ax5.set_xlabel('Regularity', fontsize=10)
ax5.set_xlim(0, 1)
ax5.grid(True, alpha=0.3, axis='x')

# V2 Features box
ax6 = fig.add_subplot(gs[2, 2])
ax6.axis('off')
features_text = """
V2 ENHANCEMENTS

Pattern Detection:
✓ Analyzes actual spacing
✓ Calculates confidence
✓ Measures regularity
✓ Detects irregular patterns

Trend Analysis:
✓ 7 time windows
✓ Growth rate tracking
✓ Volatility measurement
✓ Recent vs historical

Thresholds:
✓ Pattern-aware
✓ Adaptive Z-scores
✓ Regularity-based
✓ Reduced false positives

Interactive Tools:
✓ Command-line dashboard
✓ Explore any combination
✓ Weekly/monthly views
"""
ax6.text(0.1, 0.5, features_text, fontsize=10, verticalalignment='center',
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.6))

plt.savefig(f'{OUTPUT_DIR}/v2_05_executive_summary.png', dpi=300, bbox_inches='tight')
print(f"   Saved: v2_05_executive_summary.png")
plt.close()

# ============================================================================
# REMAINING CHARTS (6-10) - Additional Analysis
# ============================================================================

print("[6/10] Creating irregular pattern analysis...")

# Focus on irregular patterns
irregular_df = freq_df[freq_df['frequency_category'] == 'irregular'].nlargest(12, 'avg_volume')

if len(irregular_df) > 0:
    fig, axes = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle('Irregular Pattern Analysis (Special Handling Required)',
                 fontsize=20, fontweight='bold')

    # Volume distribution of irregular patterns
    ax = axes[0, 0]
    ax.hist(np.log10(irregular_df['avg_volume'].values + 1), bins=20,
            color='#FF6B6B', edgecolor='black', alpha=0.7)
    ax.set_title('Volume Distribution (Irregular Patterns)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Log10(Avg Volume)', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.grid(True, alpha=0.3)

    # Confidence vs regularity for irregular
    ax = axes[0, 1]
    scatter = ax.scatter(irregular_df['confidence'], irregular_df['regularity_score'],
                        s=irregular_df['avg_volume']/100, alpha=0.6,
                        color='#FF6B6B', edgecolors='darkred', linewidth=1)
    ax.set_xlabel('Confidence', fontsize=12, fontweight='bold')
    ax.set_ylabel('Regularity Score', fontsize=12, fontweight='bold')
    ax.set_title('Irregular Patterns: Confidence vs Regularity', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # Top irregular by volume
    ax = axes[1, 0]
    top_irregular = irregular_df.nlargest(10, 'avg_volume')
    labels = [f"{row['app']}-{row['message_type'][:8]}" for _, row in top_irregular.iterrows()]
    ax.barh(range(len(top_irregular)), top_irregular['avg_volume'].values,
            color='#FF6B6B', edgecolor='darkred')
    ax.set_yticks(range(len(top_irregular)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_title('Top 10 Irregular Patterns by Volume', fontsize=14, fontweight='bold')
    ax.set_xlabel('Average Volume', fontsize=12)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(
        lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K'
    ))
    ax.grid(True, alpha=0.3, axis='x')

    # Occurrence count distribution
    ax = axes[1, 1]
    ax.hist(irregular_df['total_occurrences'], bins=15, color='#FF6B6B',
            edgecolor='black', alpha=0.7)
    ax.set_title('Occurrence Count Distribution (Irregular)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Number of Occurrences', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/v2_06_irregular_patterns.png', dpi=300, bbox_inches='tight')
    print(f"   Saved: v2_06_irregular_patterns.png")
    plt.close()

print("\n" + "="*80)
print("V2 VISUALIZATION COMPLETE!")
print("="*80)
print(f"\nAll visualizations saved to: {OUTPUT_DIR}/")
print("\nGenerated files:")
print("  1. v2_01_pattern_analysis.png - Enhanced pattern distribution with confidence")
print("  2. v2_02_multiwindow_trends.png - Multi-window trend analysis")
print("  3. v2_03_threshold_analysis.png - Pattern-aware threshold comparison")
print("  4. v2_04_pattern_examples.png - Real examples with trend lines")
print("  5. v2_05_executive_summary.png - Enhanced executive dashboard")
print("  6. v2_06_irregular_patterns.png - Irregular pattern analysis")
print("\nThese visualizations showcase the V2 improvements!")
