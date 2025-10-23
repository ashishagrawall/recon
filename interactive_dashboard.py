"""
Interactive Volume Analysis Dashboard

Allows user to:
1. Select app and/or message type from dropdown
2. View line graph with volume over time
3. Toggle between week-by-week and month-by-month views
4. See thresholds, trends, and alerts
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.widgets import Button, CheckButtons
import seaborn as sns
from datetime import datetime
import sys


class VolumeAnalysisDashboard:
    def __init__(self, data_file):
        """Initialize dashboard with data"""
        print("Loading data...")
        self.df = pd.read_csv(data_file)
        self.df['week_start_date'] = pd.to_datetime(self.df['week_start_date'])
        self.df = self.df.sort_values('week_start_date')

        # Get unique apps and message types
        self.apps = sorted(self.df['app'].unique())
        self.message_types = sorted(self.df['message_type'].unique())

        print(f"Loaded {len(self.df)} records")
        print(f"Apps: {len(self.apps)}, Message Types: {len(self.message_types)}")

    def get_filtered_data(self, app=None, message_type=None):
        """Filter data by app and/or message type"""
        filtered = self.df.copy()

        if app and app != 'ALL':
            filtered = filtered[filtered['app'] == app]

        if message_type and message_type != 'ALL':
            filtered = filtered[filtered['message_type'] == message_type]

        return filtered.groupby('week_start_date')['volume'].sum().reset_index()

    def plot_volume_trend(self, app=None, message_type=None,
                          view_mode='weekly', show_threshold=True,
                          show_moving_avg=True, ma_window=4):
        """
        Plot volume trend with various options

        Args:
            app: App to filter (None or 'ALL' for all apps)
            message_type: Message type to filter
            view_mode: 'weekly' or 'monthly'
            show_threshold: Show threshold lines
            show_moving_avg: Show moving average
            ma_window: Moving average window (weeks)
        """
        # Get data
        data = self.get_filtered_data(app, message_type)

        if len(data) == 0:
            print("No data for selected filters")
            return

        # Aggregate by month if needed
        if view_mode == 'monthly':
            data['month'] = data['week_start_date'].dt.to_period('M')
            data = data.groupby('month')['volume'].sum().reset_index()
            data['week_start_date'] = data['month'].dt.to_timestamp()

        # Create figure
        fig, ax = plt.subplots(figsize=(16, 8))

        # Plot main line
        ax.plot(data['week_start_date'], data['volume'],
                marker='o', linewidth=2, markersize=6,
                label='Actual Volume', color='#2E86AB', zorder=3)

        # Calculate and show statistics
        mean_vol = data['volume'].mean()
        std_vol = data['volume'].std()

        # Show mean line
        ax.axhline(y=mean_vol, color='green', linestyle='--',
                   linewidth=2, label=f'Mean: {mean_vol:,.0f}', alpha=0.7, zorder=2)

        # Show threshold (mean - 2*std)
        if show_threshold:
            threshold = max(0, mean_vol - 2 * std_vol)
            ax.axhline(y=threshold, color='red', linestyle='--',
                       linewidth=2, label=f'Alert Threshold: {threshold:,.0f}',
                       alpha=0.7, zorder=2)

            # Highlight points below threshold
            below_threshold = data[data['volume'] < threshold]
            if len(below_threshold) > 0:
                ax.scatter(below_threshold['week_start_date'],
                          below_threshold['volume'],
                          color='red', s=150, zorder=5,
                          label=f'Below Threshold ({len(below_threshold)} alerts)',
                          marker='X', edgecolors='darkred', linewidth=2)

        # Show moving average
        if show_moving_avg and len(data) >= ma_window:
            data['ma'] = data['volume'].rolling(window=ma_window, min_periods=1).mean()
            ax.plot(data['week_start_date'], data['ma'],
                    linewidth=2.5, label=f'{ma_window}-Week Moving Avg',
                    color='orange', alpha=0.8, zorder=2)

        # Formatting
        title = "Volume Trend Analysis"
        if app and app != 'ALL':
            title += f" - {app}"
        if message_type and message_type != 'ALL':
            title += f" - {message_type}"
        title += f" ({view_mode.capitalize()} View)"

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Volume', fontsize=12, fontweight='bold')

        # Format y-axis
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{int(x/1e6)}M' if x >= 1e6 else f'{int(x/1e3)}K' if x >= 1e3 else f'{int(x)}'
        ))

        # Format x-axis
        if view_mode == 'weekly':
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        else:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        plt.xticks(rotation=45, ha='right')

        # Grid
        ax.grid(True, alpha=0.3, zorder=1)

        # Legend
        ax.legend(loc='best', fontsize=10, framealpha=0.9)

        # Add statistics box
        stats_text = f"Data Points: {len(data)}\n"
        stats_text += f"Mean: {mean_vol:,.0f}\n"
        stats_text += f"Std Dev: {std_vol:,.0f}\n"
        stats_text += f"Min: {data['volume'].min():,.0f}\n"
        stats_text += f"Max: {data['volume'].max():,.0f}\n"
        stats_text += f"CV: {(std_vol/mean_vol):.2f}"

        ax.text(0.02, 0.98, stats_text,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.tight_layout()
        return fig, ax

    def plot_comparison_all_apps(self, message_type):
        """Plot comparison of all apps for a specific message type"""
        fig, ax = plt.subplots(figsize=(16, 10))

        filtered = self.df[self.df['message_type'] == message_type]
        apps_with_data = filtered['app'].unique()

        colors = plt.cm.tab20(np.linspace(0, 1, len(apps_with_data)))

        for idx, app in enumerate(apps_with_data):
            app_data = filtered[filtered['app'] == app].groupby('week_start_date')['volume'].sum().reset_index()
            ax.plot(app_data['week_start_date'], app_data['volume'],
                    marker='o', linewidth=1.5, markersize=4,
                    label=app, color=colors[idx], alpha=0.7)

        ax.set_title(f'Volume Comparison - All Apps for {message_type}',
                     fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Volume', fontsize=12)
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), ncol=1, fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig, ax


def interactive_menu(data_file):
    """Interactive command-line menu for exploring data"""
    dashboard = VolumeAnalysisDashboard(data_file)

    while True:
        print("\n" + "="*80)
        print("INTERACTIVE VOLUME ANALYSIS DASHBOARD")
        print("="*80)
        print("\n1. Analyze specific App + Message Type")
        print("2. Analyze all apps for a Message Type")
        print("3. Analyze all message types for an App")
        print("4. Compare apps for a message type")
        print("5. Exit")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == '5':
            print("Exiting...")
            break

        elif choice == '1':
            # Select app
            print(f"\nAvailable apps: {', '.join(dashboard.apps[:10])}...")
            app = input("Enter app name (or 'ALL'): ").strip().upper()

            # Select message type
            print(f"\nAvailable message types: {', '.join(dashboard.message_types[:10])}...")
            msg_type = input("Enter message type (or 'ALL'): ").strip().upper()

            # View mode
            view = input("View mode (weekly/monthly) [weekly]: ").strip().lower() or 'weekly'

            # MA window
            ma_win = input("Moving average window in weeks [4]: ").strip() or '4'

            print("\nGenerating plot...")
            fig, ax = dashboard.plot_volume_trend(
                app=app if app != 'ALL' else None,
                message_type=msg_type if msg_type != 'ALL' else None,
                view_mode=view,
                show_threshold=True,
                show_moving_avg=True,
                ma_window=int(ma_win)
            )

            if fig:
                plt.show()

        elif choice == '2':
            print(f"\nAvailable message types: {', '.join(dashboard.message_types[:10])}...")
            msg_type = input("Enter message type: ").strip().upper()

            view = input("View mode (weekly/monthly) [weekly]: ").strip().lower() or 'weekly'

            print("\nGenerating plot...")
            fig, ax = dashboard.plot_volume_trend(
                app=None,
                message_type=msg_type,
                view_mode=view
            )

            if fig:
                plt.show()

        elif choice == '3':
            print(f"\nAvailable apps: {', '.join(dashboard.apps[:10])}...")
            app = input("Enter app name: ").strip().upper()

            view = input("View mode (weekly/monthly) [weekly]: ").strip().lower() or 'weekly'

            print("\nGenerating plot...")
            fig, ax = dashboard.plot_volume_trend(
                app=app,
                message_type=None,
                view_mode=view
            )

            if fig:
                plt.show()

        elif choice == '4':
            print(f"\nAvailable message types: {', '.join(dashboard.message_types[:10])}...")
            msg_type = input("Enter message type: ").strip().upper()

            print("\nGenerating comparison plot...")
            fig, ax = dashboard.plot_comparison_all_apps(msg_type)

            if fig:
                plt.show()

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    data_file = '/Users/ashishagrawal-mac16/Documents/recon/payment_screening_volumes.csv'

    print("\n" + "="*80)
    print("PAYMENT SCREENING VOLUME ANALYSIS - INTERACTIVE DASHBOARD")
    print("="*80)

    interactive_menu(data_file)
