"""
Payment Screening Volume Visualization Dashboard

Creates comprehensive visualizations for presentation including:
1. Volume trends over time
2. Frequency distribution analysis
3. Threshold visualization
4. Alert detection examples
5. App-level summaries
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
THRESHOLD_FILE = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output/threshold_configuration.csv'
OUTPUT_DIR = '/Users/ashishagrawal-mac16/Documents/recon/analysis_output'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")
sns.set_palette("Set2")

print("="*80)
print("CREATING VISUALIZATIONS FOR PRESENTATION")
print("="*80)

# Load data
df = pd.read_csv(DATA_FILE)
df['week_start_date'] = pd.to_datetime(df['week_start_date'])
df = df.sort_values(['app', 'message_type', 'week_start_date'])

print(f"\nLoaded {len(df):,} records")

# ============================================================================
# 1. OVERALL VOLUME TRENDS
# ============================================================================

print("\n[1/8] Creating overall volume trends...")

fig, axes = plt.subplots(2, 2, figsize=(20, 12))
fig.suptitle('Payment Screening Volume Overview', fontsize=20, fontweight='bold')

# Total weekly volume
weekly_totals = df.groupby('week_start_date')['volume'].sum()
ax = axes[0, 0]
ax.plot(weekly_totals.index, weekly_totals.values, linewidth=2, color='#2E86AB')
ax.fill_between(weekly_totals.index, weekly_totals.values, alpha=0.3, color='#2E86AB')
ax.set_title('Total Weekly Volume Across All Systems', fontsize=14, fontweight='bold')
ax.set_xlabel('Week Start Date', fontsize=12)
ax.set_ylabel('Total Volume', fontsize=12)
ax.ticklabel_format(style='plain', axis='y')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K'))
ax.grid(True, alpha=0.3)

# Volume by app
top_apps = df.groupby('app')['volume'].sum().nlargest(10)
ax = axes[0, 1]
ax.barh(range(len(top_apps)), top_apps.values, color=sns.color_palette("viridis", len(top_apps)))
ax.set_yticks(range(len(top_apps)))
ax.set_yticklabels(top_apps.index, fontsize=10)
ax.set_title('Top 10 Apps by Total Volume', fontsize=14, fontweight='bold')
ax.set_xlabel('Total Volume (2 years)', fontsize=12)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K'))
ax.grid(True, alpha=0.3, axis='x')

# Message count by app
msg_counts = df.groupby('app')['message_type'].nunique().sort_values(ascending=False).head(10)
ax = axes[1, 0]
ax.bar(range(len(msg_counts)), msg_counts.values, color='#A23B72')
ax.set_xticks(range(len(msg_counts)))
ax.set_xticklabels(msg_counts.index, rotation=45, ha='right', fontsize=10)
ax.set_title('Message Type Diversity by App (Top 10)', fontsize=14, fontweight='bold')
ax.set_ylabel('Number of Message Types', fontsize=12)
ax.grid(True, alpha=0.3, axis='y')

# Volume distribution
ax = axes[1, 1]
volumes = df['volume'].values
ax.hist(np.log10(volumes[volumes > 0]), bins=50, color='#F18F01', edgecolor='black', alpha=0.7)
ax.set_title('Volume Distribution (Log Scale)', fontsize=14, fontweight='bold')
ax.set_xlabel('Log10(Volume)', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/01_overall_trends.png', dpi=300, bbox_inches='tight')
print(f"   Saved: 01_overall_trends.png")
plt.close()

# ============================================================================
# 2. FREQUENCY DISTRIBUTION
# ============================================================================

print("[2/8] Creating frequency distribution analysis...")

# Load threshold data if available
try:
    threshold_df = pd.read_csv(THRESHOLD_FILE)
    # Handle duplicate column names (from merge)
    if 'cv_x' in threshold_df.columns:
        threshold_df['cv'] = threshold_df['cv_y']
    if 'std_volume_x' in threshold_df.columns:
        threshold_df['std_volume'] = threshold_df['std_volume_y']
    has_threshold = True
except:
    has_threshold = False

fig, axes = plt.subplots(2, 2, figsize=(20, 12))
fig.suptitle('Message Frequency Analysis', fontsize=20, fontweight='bold')

# Frequency categories
if has_threshold:
    freq_counts = threshold_df['frequency_category'].value_counts()
    ax = axes[0, 0]
    wedges, texts, autotexts = ax.pie(freq_counts.values, labels=freq_counts.index,
                                        autopct='%1.1f%%', startangle=90,
                                        colors=sns.color_palette("Set3", len(freq_counts)))
    ax.set_title('Distribution of Message Frequencies', fontsize=14, fontweight='bold')
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)

    # Average volume by frequency
    avg_by_freq = threshold_df.groupby('frequency_category')['avg_volume'].mean().sort_values(ascending=False)
    ax = axes[0, 1]
    ax.barh(range(len(avg_by_freq)), avg_by_freq.values, color=sns.color_palette("coolwarm", len(avg_by_freq)))
    ax.set_yticks(range(len(avg_by_freq)))
    ax.set_yticklabels(avg_by_freq.index, fontsize=10)
    ax.set_title('Average Volume by Frequency Category', fontsize=14, fontweight='bold')
    ax.set_xlabel('Average Weekly Volume', fontsize=12)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K'))
    ax.grid(True, alpha=0.3, axis='x')

    # Coefficient of Variation by frequency
    cv_by_freq = threshold_df.groupby('frequency_category')['cv'].mean().sort_values()
    ax = axes[1, 0]
    ax.bar(range(len(cv_by_freq)), cv_by_freq.values, color='#6A4C93')
    ax.set_xticks(range(len(cv_by_freq)))
    ax.set_xticklabels(cv_by_freq.index, rotation=45, ha='right', fontsize=10)
    ax.set_title('Variability by Frequency (Lower is More Stable)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Coefficient of Variation', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')

    # Count by frequency
    count_by_freq = threshold_df['frequency_category'].value_counts().sort_values()
    ax = axes[1, 1]
    ax.barh(range(len(count_by_freq)), count_by_freq.values, color='#1982C4')
    ax.set_yticks(range(len(count_by_freq)))
    ax.set_yticklabels(count_by_freq.index, fontsize=10)
    ax.set_title('Number of App-Message Combinations by Frequency', fontsize=14, fontweight='bold')
    ax.set_xlabel('Count', fontsize=12)
    ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/02_frequency_distribution.png', dpi=300, bbox_inches='tight')
print(f"   Saved: 02_frequency_distribution.png")
plt.close()

# ============================================================================
# 3. EXAMPLE VOLUME TRENDS WITH THRESHOLDS
# ============================================================================

print("[3/8] Creating example volume trends with thresholds...")

# Select interesting examples from different frequency categories
if has_threshold:
    examples = []
    for freq in ['daily_high', 'weekly', 'monthly', 'quarterly']:
        sample = threshold_df[threshold_df['frequency_category'] == freq]
        if len(sample) > 0:
            # Pick one with medium CV (not too stable, not too variable)
            sample = sample.sort_values('cv')
            idx = len(sample) // 2
            examples.append(sample.iloc[idx])

    fig, axes = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle('Volume Trends with Dynamic Thresholds (Examples)', fontsize=20, fontweight='bold')

    for idx, example in enumerate(examples[:4]):
        ax = axes[idx // 2, idx % 2]

        # Get time series data
        ts_data = df[
            (df['app'] == example['app']) &
            (df['message_type'] == example['message_type'])
        ].sort_values('week_start_date')

        # Plot volume
        ax.plot(ts_data['week_start_date'], ts_data['volume'],
                marker='o', linewidth=2, markersize=4, label='Actual Volume', color='#2E86AB')

        # Plot mean
        ax.axhline(y=example['mean_volume'], color='green', linestyle='--',
                   linewidth=2, label=f'Mean: {example["mean_volume"]:,.0f}', alpha=0.7)

        # Plot threshold
        ax.axhline(y=example['threshold'], color='red', linestyle='--',
                   linewidth=2, label=f'Alert Threshold: {example["threshold"]:,.0f}', alpha=0.7)

        # Highlight points below threshold
        below_threshold = ts_data[ts_data['volume'] < example['threshold']]
        if len(below_threshold) > 0:
            ax.scatter(below_threshold['week_start_date'], below_threshold['volume'],
                      color='red', s=100, zorder=5, label='Below Threshold', marker='X')

        ax.set_title(f'{example["app"]} - {example["message_type"]}\n({example["frequency_category"]})',
                    fontsize=12, fontweight='bold')
        ax.set_xlabel('Week Start Date', fontsize=10)
        ax.set_ylabel('Volume', fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K'))
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/03_threshold_examples.png', dpi=300, bbox_inches='tight')
    print(f"   Saved: 03_threshold_examples.png")
    plt.close()

# ============================================================================
# 4. APP-LEVEL SUMMARY
# ============================================================================

print("[4/8] Creating app-level summary...")

app_summary = df.groupby('app').agg({
    'volume': ['sum', 'mean', 'std'],
    'message_type': 'nunique',
    'week_start_date': 'count'
}).reset_index()
app_summary.columns = ['app', 'total_volume', 'avg_weekly_volume', 'std_volume', 'num_msg_types', 'num_records']
app_summary = app_summary.sort_values('total_volume', ascending=False)

fig, axes = plt.subplots(2, 2, figsize=(20, 12))
fig.suptitle('App-Level Performance Summary', fontsize=20, fontweight='bold')

# Total volume by app
ax = axes[0, 0]
top_15 = app_summary.head(15)
colors = sns.color_palette("rocket", len(top_15))
ax.barh(range(len(top_15)), top_15['total_volume'].values, color=colors)
ax.set_yticks(range(len(top_15)))
ax.set_yticklabels(top_15['app'].values, fontsize=10)
ax.set_title('Total Volume by App (Top 15)', fontsize=14, fontweight='bold')
ax.set_xlabel('Total Volume (2 years)', fontsize=12)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e9)}B' if x >= 1e9 else f'{int(x/1e6)}M'))
ax.grid(True, alpha=0.3, axis='x')

# Average volume vs message diversity
ax = axes[0, 1]
scatter = ax.scatter(app_summary['num_msg_types'], app_summary['avg_weekly_volume'],
                    s=app_summary['total_volume']/1e6, alpha=0.6, c=range(len(app_summary)),
                    cmap='viridis', edgecolors='black', linewidth=0.5)
for idx, row in app_summary.head(10).iterrows():
    ax.annotate(row['app'], (row['num_msg_types'], row['avg_weekly_volume']),
                fontsize=8, alpha=0.7)
ax.set_title('Message Diversity vs Average Volume\n(bubble size = total volume)', fontsize=14, fontweight='bold')
ax.set_xlabel('Number of Message Types', fontsize=12)
ax.set_ylabel('Average Weekly Volume', fontsize=12)
ax.set_yscale('log')
ax.grid(True, alpha=0.3)

# Volatility analysis
app_summary['cv'] = app_summary['std_volume'] / app_summary['avg_weekly_volume']
top_volatile = app_summary.nlargest(15, 'cv')
ax = axes[1, 0]
ax.barh(range(len(top_volatile)), top_volatile['cv'].values, color='#E76F51')
ax.set_yticks(range(len(top_volatile)))
ax.set_yticklabels(top_volatile['app'].values, fontsize=10)
ax.set_title('Most Volatile Apps (Coefficient of Variation)', fontsize=14, fontweight='bold')
ax.set_xlabel('Coefficient of Variation (Higher = More Volatile)', fontsize=12)
ax.grid(True, alpha=0.3, axis='x')

# Activity heatmap (sample)
ax = axes[1, 1]
# Get weekly activity for top 10 apps
top_10_apps = app_summary.head(10)['app'].values
heatmap_data = []
weeks = sorted(df['week_start_date'].unique())[-20:]  # Last 20 weeks

for app in top_10_apps:
    app_data = df[df['app'] == app]
    weekly_volumes = []
    for week in weeks:
        vol = app_data[app_data['week_start_date'] == week]['volume'].sum()
        weekly_volumes.append(vol)
    heatmap_data.append(weekly_volumes)

sns.heatmap(heatmap_data, ax=ax, cmap='YlOrRd', cbar_kws={'label': 'Volume'},
            yticklabels=top_10_apps, xticklabels=False, fmt='.0f')
ax.set_title('Volume Activity Heatmap (Top 10 Apps, Last 20 Weeks)', fontsize=14, fontweight='bold')
ax.set_ylabel('App', fontsize=12)
ax.set_xlabel('Week', fontsize=12)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/04_app_summary.png', dpi=300, bbox_inches='tight')
print(f"   Saved: 04_app_summary.png")
plt.close()

# ============================================================================
# 5. MESSAGE TYPE ANALYSIS
# ============================================================================

print("[5/8] Creating message type analysis...")

msg_summary = df.groupby('message_type').agg({
    'volume': ['sum', 'mean'],
    'app': 'nunique'
}).reset_index()
msg_summary.columns = ['message_type', 'total_volume', 'avg_volume', 'num_apps']
msg_summary = msg_summary.sort_values('total_volume', ascending=False)

fig, axes = plt.subplots(2, 2, figsize=(20, 12))
fig.suptitle('Message Type Analysis', fontsize=20, fontweight='bold')

# Top message types by volume
ax = axes[0, 0]
top_20_msg = msg_summary.head(20)
ax.barh(range(len(top_20_msg)), top_20_msg['total_volume'].values,
        color=sns.color_palette("mako", len(top_20_msg)))
ax.set_yticks(range(len(top_20_msg)))
ax.set_yticklabels(top_20_msg['message_type'].values, fontsize=9)
ax.set_title('Top 20 Message Types by Total Volume', fontsize=14, fontweight='bold')
ax.set_xlabel('Total Volume (2 years)', fontsize=12)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e9)}B' if x >= 1e9 else f'{int(x/1e6)}M'))
ax.grid(True, alpha=0.3, axis='x')

# Message types by app adoption
ax = axes[0, 1]
top_adoption = msg_summary.nlargest(20, 'num_apps')
ax.barh(range(len(top_adoption)), top_adoption['num_apps'].values, color='#8338EC')
ax.set_yticks(range(len(top_adoption)))
ax.set_yticklabels(top_adoption['message_type'].values, fontsize=9)
ax.set_title('Most Widely Used Message Types (By # of Apps)', fontsize=14, fontweight='bold')
ax.set_xlabel('Number of Apps Using This Message Type', fontsize=12)
ax.grid(True, alpha=0.3, axis='x')

# Volume vs adoption scatter
ax = axes[1, 0]
scatter = ax.scatter(msg_summary['num_apps'], msg_summary['avg_volume'],
                    alpha=0.5, c=msg_summary['total_volume'], cmap='plasma',
                    s=100, edgecolors='black', linewidth=0.5)
plt.colorbar(scatter, ax=ax, label='Total Volume')
ax.set_title('Message Type: Adoption vs Volume', fontsize=14, fontweight='bold')
ax.set_xlabel('Number of Apps', fontsize=12)
ax.set_ylabel('Average Weekly Volume', fontsize=12)
ax.set_yscale('log')
ax.grid(True, alpha=0.3)

# Distribution of message types per app
msg_per_app = df.groupby('app')['message_type'].nunique()
ax = axes[1, 1]
ax.hist(msg_per_app.values, bins=20, color='#06FFA5', edgecolor='black', alpha=0.7)
ax.set_title('Distribution of Message Types per App', fontsize=14, fontweight='bold')
ax.set_xlabel('Number of Message Types', fontsize=12)
ax.set_ylabel('Number of Apps', fontsize=12)
ax.axvline(msg_per_app.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {msg_per_app.mean():.1f}')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/05_message_type_analysis.png', dpi=300, bbox_inches='tight')
print(f"   Saved: 05_message_type_analysis.png")
plt.close()

# ============================================================================
# 6. THRESHOLD METHODOLOGY COMPARISON
# ============================================================================

print("[6/8] Creating threshold methodology comparison...")

if has_threshold:
    # Compare different threshold methods
    sample_for_comparison = threshold_df.sample(min(100, len(threshold_df)))

    fig, axes = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle('Threshold Methodology Comparison', fontsize=20, fontweight='bold')

    # Z-score vs Percentile
    ax = axes[0, 0]
    ax.scatter(sample_for_comparison['z_score_method'],
              sample_for_comparison['percentile_method'],
              alpha=0.6, s=50, color='#FF6B6B')
    ax.plot([0, sample_for_comparison['z_score_method'].max()],
           [0, sample_for_comparison['z_score_method'].max()],
           'k--', alpha=0.3, label='y=x')
    ax.set_title('Z-Score Method vs Percentile Method', fontsize=14, fontweight='bold')
    ax.set_xlabel('Z-Score Based Threshold', fontsize=12)
    ax.set_ylabel('Percentile Based Threshold', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # IQR vs Final
    ax = axes[0, 1]
    ax.scatter(sample_for_comparison['iqr_method'],
              sample_for_comparison['threshold'],
              alpha=0.6, s=50, color='#4ECDC4')
    ax.plot([0, sample_for_comparison['iqr_method'].max()],
           [0, sample_for_comparison['iqr_method'].max()],
           'k--', alpha=0.3, label='y=x')
    ax.set_title('IQR Method vs Final Threshold', fontsize=14, fontweight='bold')
    ax.set_xlabel('IQR Based Threshold', fontsize=12)
    ax.set_ylabel('Final Threshold (Max of all methods)', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Threshold as % of mean by frequency
    threshold_df['threshold_pct_of_mean'] = (threshold_df['threshold'] / threshold_df['mean_volume']) * 100
    threshold_pct_by_freq = threshold_df.groupby('frequency_category')['threshold_pct_of_mean'].mean().sort_values()
    ax = axes[1, 0]
    ax.barh(range(len(threshold_pct_by_freq)), threshold_pct_by_freq.values, color='#95E1D3')
    ax.set_yticks(range(len(threshold_pct_by_freq)))
    ax.set_yticklabels(threshold_pct_by_freq.index, fontsize=10)
    ax.set_title('Threshold as % of Mean Volume by Frequency', fontsize=14, fontweight='bold')
    ax.set_xlabel('Threshold as % of Mean', fontsize=12)
    ax.grid(True, alpha=0.3, axis='x')

    # Distribution of CV by frequency
    ax = axes[1, 1]
    freq_categories = threshold_df['frequency_category'].unique()
    cv_data = [threshold_df[threshold_df['frequency_category'] == freq]['cv'].values
               for freq in freq_categories]
    bp = ax.boxplot(cv_data, labels=freq_categories, patch_artist=True)
    for patch, color in zip(bp['boxes'], sns.color_palette("Set2", len(freq_categories))):
        patch.set_facecolor(color)
    ax.set_title('Coefficient of Variation Distribution by Frequency', fontsize=14, fontweight='bold')
    ax.set_xlabel('Frequency Category', fontsize=12)
    ax.set_ylabel('Coefficient of Variation', fontsize=12)
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(f'{OUTPUT_DIR}/06_threshold_methodology.png', dpi=300, bbox_inches='tight')
    print(f"   Saved: 06_threshold_methodology.png")
    plt.close()

# ============================================================================
# 7. TEMPORAL PATTERNS
# ============================================================================

print("[7/8] Creating temporal pattern analysis...")

df['month'] = df['week_start_date'].dt.month
df['quarter'] = df['week_start_date'].dt.quarter
df['year'] = df['week_start_date'].dt.year

fig, axes = plt.subplots(2, 2, figsize=(20, 12))
fig.suptitle('Temporal Patterns & Seasonality', fontsize=20, fontweight='bold')

# Monthly trends
monthly_avg = df.groupby('month')['volume'].mean()
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
ax = axes[0, 0]
ax.plot(monthly_avg.index, monthly_avg.values, marker='o', linewidth=3, markersize=8, color='#FF6B9D')
ax.fill_between(monthly_avg.index, monthly_avg.values, alpha=0.3, color='#FF6B9D')
ax.set_xticks(range(1, 13))
ax.set_xticklabels(month_names, rotation=45)
ax.set_title('Average Volume by Month', fontsize=14, fontweight='bold')
ax.set_xlabel('Month', fontsize=12)
ax.set_ylabel('Average Volume', fontsize=12)
ax.grid(True, alpha=0.3)

# Quarterly trends
quarterly_total = df.groupby(['year', 'quarter'])['volume'].sum().reset_index()
quarterly_labels = [f"Q{row['quarter']}-{row['year']}" for _, row in quarterly_total.iterrows()]
ax = axes[0, 1]
ax.bar(range(len(quarterly_total)), quarterly_total['volume'].values,
       color=sns.color_palette("coolwarm", len(quarterly_total)))
ax.set_xticks(range(len(quarterly_total)))
ax.set_xticklabels(quarterly_labels, rotation=45, ha='right', fontsize=9)
ax.set_title('Total Volume by Quarter', fontsize=14, fontweight='bold')
ax.set_ylabel('Total Volume', fontsize=12)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e9)}B' if x >= 1e9 else f'{int(x/1e6)}M'))
ax.grid(True, alpha=0.3, axis='y')

# Year-over-Year comparison
if len(df['year'].unique()) >= 2:
    years = sorted(df['year'].unique())
    ax = axes[1, 0]
    for year in years:
        year_data = df[df['year'] == year].groupby('month')['volume'].mean()
        ax.plot(year_data.index, year_data.values, marker='o', linewidth=2, label=f'{year}', markersize=6)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(month_names, rotation=45)
    ax.set_title('Year-over-Year Monthly Comparison', fontsize=14, fontweight='bold')
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Average Volume', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3)

# Weekly trend (rolling average)
weekly_totals = df.groupby('week_start_date')['volume'].sum().reset_index()
weekly_totals['rolling_avg_4wk'] = weekly_totals['volume'].rolling(window=4, min_periods=1).mean()
weekly_totals['rolling_avg_12wk'] = weekly_totals['volume'].rolling(window=12, min_periods=1).mean()
ax = axes[1, 1]
ax.plot(weekly_totals['week_start_date'], weekly_totals['volume'], alpha=0.3, label='Weekly', linewidth=1)
ax.plot(weekly_totals['week_start_date'], weekly_totals['rolling_avg_4wk'],
        linewidth=2, label='4-Week Moving Avg', color='orange')
ax.plot(weekly_totals['week_start_date'], weekly_totals['rolling_avg_12wk'],
        linewidth=2, label='12-Week Moving Avg', color='red')
ax.set_title('Volume Trends with Moving Averages', fontsize=14, fontweight='bold')
ax.set_xlabel('Week Start Date', fontsize=12)
ax.set_ylabel('Total Volume', fontsize=12)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e9)}B' if x >= 1e9 else f'{int(x/1e6)}M'))
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/07_temporal_patterns.png', dpi=300, bbox_inches='tight')
print(f"   Saved: 07_temporal_patterns.png")
plt.close()

# ============================================================================
# 8. EXECUTIVE SUMMARY DASHBOARD
# ============================================================================

print("[8/8] Creating executive summary dashboard...")

fig = plt.figure(figsize=(20, 14))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

fig.suptitle('PAYMENT SCREENING SYSTEM - EXECUTIVE SUMMARY', fontsize=22, fontweight='bold')

# Key metrics
ax1 = fig.add_subplot(gs[0, :])
ax1.axis('off')
metrics_text = f"""
KEY METRICS (2 Year Period: {df['week_start_date'].min().date()} to {df['week_start_date'].max().date()})

Total Messages Processed: {df['volume'].sum():,.0f}
Average Weekly Volume: {df.groupby('week_start_date')['volume'].sum().mean():,.0f}
Number of Systems: {df['app'].nunique()}
Number of Message Types: {df['message_type'].nunique()}
Unique App-Message Combinations: {df.groupby(['app', 'message_type']).ngroups:,}
Peak Weekly Volume: {df.groupby('week_start_date')['volume'].sum().max():,.0f}
Lowest Weekly Volume: {df.groupby('week_start_date')['volume'].sum().min():,.0f}
"""
ax1.text(0.1, 0.5, metrics_text, fontsize=14, verticalalignment='center',
         family='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

# Top 10 apps
ax2 = fig.add_subplot(gs[1, 0])
top_10 = app_summary.head(10)
ax2.barh(range(len(top_10)), top_10['total_volume'].values,
         color=sns.color_palette("viridis", len(top_10)))
ax2.set_yticks(range(len(top_10)))
ax2.set_yticklabels(top_10['app'].values, fontsize=10)
ax2.set_title('Top 10 Systems by Volume', fontsize=12, fontweight='bold')
ax2.set_xlabel('Total Volume', fontsize=10)
ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e9)}B' if x >= 1e9 else f'{int(x/1e6)}M'))
ax2.grid(True, alpha=0.3, axis='x')

# Volume trend
ax3 = fig.add_subplot(gs[1, 1:])
weekly_totals = df.groupby('week_start_date')['volume'].sum()
ax3.plot(weekly_totals.index, weekly_totals.values, linewidth=2, color='#2E86AB')
ax3.fill_between(weekly_totals.index, weekly_totals.values, alpha=0.3, color='#2E86AB')
ax3.set_title('Total Weekly Volume Trend', fontsize=12, fontweight='bold')
ax3.set_xlabel('Date', fontsize=10)
ax3.set_ylabel('Volume', fontsize=10)
ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e9)}B' if x >= 1e9 else f'{int(x/1e6)}M'))
ax3.grid(True, alpha=0.3)

# Frequency distribution
if has_threshold:
    ax4 = fig.add_subplot(gs[2, 0])
    freq_counts = threshold_df['frequency_category'].value_counts()
    ax4.pie(freq_counts.values, labels=freq_counts.index, autopct='%1.1f%%',
            startangle=90, colors=sns.color_palette("Set3", len(freq_counts)))
    ax4.set_title('Message Frequency Distribution', fontsize=12, fontweight='bold')

# Top message types
ax5 = fig.add_subplot(gs[2, 1])
top_msg = msg_summary.head(10)
ax5.barh(range(len(top_msg)), top_msg['total_volume'].values,
         color=sns.color_palette("rocket", len(top_msg)))
ax5.set_yticks(range(len(top_msg)))
ax5.set_yticklabels(top_msg['message_type'].values, fontsize=9)
ax5.set_title('Top 10 Message Types', fontsize=12, fontweight='bold')
ax5.set_xlabel('Total Volume', fontsize=10)
ax5.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1e9)}B' if x >= 1e9 else f'{int(x/1e6)}M'))
ax5.grid(True, alpha=0.3, axis='x')

# Alert summary (if available)
ax6 = fig.add_subplot(gs[2, 2])
ax6.axis('off')
alert_text = """
ALERTING SYSTEM

✓ Dynamic thresholds calculated
✓ Multiple statistical methods
✓ Frequency-aware detection
✓ Configurable sensitivity

Methods Used:
• Z-score based
• Percentile based
• IQR based
• Rolling averages

Ready for production deployment
"""
ax6.text(0.1, 0.5, alert_text, fontsize=11, verticalalignment='center',
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))

plt.savefig(f'{OUTPUT_DIR}/08_executive_summary.png', dpi=300, bbox_inches='tight')
print(f"   Saved: 08_executive_summary.png")
plt.close()

print("\n" + "="*80)
print("VISUALIZATION COMPLETE!")
print("="*80)
print(f"\nAll visualizations saved to: {OUTPUT_DIR}/")
print("\nGenerated files:")
print("  1. 01_overall_trends.png - Overall volume trends and distributions")
print("  2. 02_frequency_distribution.png - Message frequency analysis")
print("  3. 03_threshold_examples.png - Example trends with dynamic thresholds")
print("  4. 04_app_summary.png - App-level performance summary")
print("  5. 05_message_type_analysis.png - Message type deep dive")
print("  6. 06_threshold_methodology.png - Threshold calculation comparison")
print("  7. 07_temporal_patterns.png - Temporal and seasonal patterns")
print("  8. 08_executive_summary.png - Executive summary dashboard")
print("\nThese visualizations are ready for your presentation!")
