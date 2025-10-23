import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_APPS = 26
NUM_MESSAGE_TYPES = 355
NUM_WEEKS = 104  # 2 years of weekly data

# Generate app names
apps = [f"APP_{i:02d}" for i in range(1, NUM_APPS + 1)]

# Generate message types (SWIFT and non-SWIFT)
swift_message_types = [f"MT{random.randint(100, 999)}" for _ in range(150)]
non_swift_message_types = [f"MX{random.randint(1000, 9999)}" for _ in range(150)]
custom_message_types = [f"CUSTOM_{i:03d}" for i in range(1, 56)]
message_types = swift_message_types + non_swift_message_types + custom_message_types

# Generate week start dates (every Monday for last 2 years)
end_date = datetime.now()
# Go back to most recent Monday
days_since_monday = end_date.weekday()
last_monday = end_date - timedelta(days=days_since_monday)
week_start_dates = [last_monday - timedelta(weeks=i) for i in range(NUM_WEEKS)]
week_start_dates.reverse()

# Define frequency patterns with realistic payment screening volumes
FREQUENCIES = {
    'daily_high': {'probability': 1.0, 'base_volume': (5000000, 20000000), 'variance': 0.10},  # Very high volume, low variance
    'daily_medium': {'probability': 1.0, 'base_volume': (500000, 5000000), 'variance': 0.15},  # High volume
    'daily_low': {'probability': 1.0, 'base_volume': (50000, 500000), 'variance': 0.20},  # Medium volume
    'weekly': {'probability': 0.95, 'base_volume': (10000, 200000), 'variance': 0.25},
    'biweekly': {'probability': 0.5, 'base_volume': (5000, 50000), 'variance': 0.30},
    'monthly': {'probability': 0.23, 'base_volume': (1000, 10000), 'variance': 0.35},  # ~1 per month
    'quarterly': {'probability': 0.08, 'base_volume': (500, 5000), 'variance': 0.40},  # ~1 per quarter
    'semi_annual': {'probability': 0.02, 'base_volume': (300, 2000), 'variance': 0.45},  # ~2 per year
}

# Assign frequency patterns to app-message type combinations
def assign_frequency_pattern():
    """Randomly assign frequency pattern with realistic distribution"""
    rand = random.random()
    if rand < 0.20:  # 20% very high daily volume (millions)
        return 'daily_high'
    elif rand < 0.40:  # 20% medium daily volume
        return 'daily_medium'
    elif rand < 0.55:  # 15% low daily volume
        return 'daily_low'
    elif rand < 0.70:  # 15% weekly
        return 'weekly'
    elif rand < 0.82:  # 12% biweekly
        return 'biweekly'
    elif rand < 0.92:  # 10% monthly
        return 'monthly'
    elif rand < 0.97:  # 5% quarterly
        return 'quarterly'
    else:  # 3% semi-annual
        return 'semi_annual'

# Create mapping of app-message_type to frequency pattern
app_msg_config = {}

# Identify high-volume apps (send all messages daily)
high_volume_apps = random.sample(apps, 5)  # 5 apps send all messages daily

for app in apps:
    num_msg_types_for_app = random.randint(5, 80)  # Each app handles 5-80 message types
    selected_msg_types = random.sample(message_types, num_msg_types_for_app)

    for msg_type in selected_msg_types:
        # High volume apps send all messages daily
        if app in high_volume_apps:
            # Mix of high and medium volumes for high-volume apps
            if random.random() < 0.6:  # 60% in millions
                frequency = 'daily_high'
            else:  # 40% in hundreds of thousands
                frequency = 'daily_medium'
        else:
            # Other apps have variable frequencies
            frequency = assign_frequency_pattern()

        base_vol_range = FREQUENCIES[frequency]['base_volume']
        base_volume = random.randint(base_vol_range[0], base_vol_range[1])

        app_msg_config[(app, msg_type)] = {
            'frequency': frequency,
            'base_volume': base_volume,
            'variance': FREQUENCIES[frequency]['variance'],
            'probability': FREQUENCIES[frequency]['probability']
        }

print(f"Total unique app-message type combinations: {len(app_msg_config)}")
print(f"High-volume apps (daily all messages): {high_volume_apps}")

# Generate the data
data_records = []

for week_start in week_start_dates:
    week_str = week_start.strftime('%Y-%m-%d')

    for (app, msg_type), config in app_msg_config.items():
        # Determine if message occurs this week based on frequency probability
        if random.random() > config['probability']:
            continue  # Skip this week

        # Generate volume with random variance
        base_vol = config['base_volume']
        variance = config['variance']

        # Add realistic variance (normal distribution)
        volume = int(base_vol * (1 + np.random.normal(0, variance)))

        # Ensure non-negative volume
        volume = max(0, volume)

        # Occasionally add anomalies (5% chance of significant drop or spike)
        if random.random() < 0.05:
            if random.random() < 0.5:
                volume = int(volume * random.uniform(0.1, 0.5))  # Significant drop
            else:
                volume = int(volume * random.uniform(1.5, 3.0))  # Spike

        data_records.append({
            'app': app,
            'message_type': msg_type,
            'week_start_date': week_str,
            'volume': volume
        })

# Create DataFrame
df = pd.DataFrame(data_records)

# Sort by app, message_type, week_start_date
df = df.sort_values(['app', 'message_type', 'week_start_date']).reset_index(drop=True)

# Save to CSV
output_file = '/Users/ashishagrawal-mac16/Documents/recon/payment_screening_volumes.csv'
df.to_csv(output_file, index=False)

print(f"\nData generated successfully!")
print(f"Output file: {output_file}")
print(f"\nDataset summary:")
print(f"  Total records: {len(df):,}")
print(f"  Date range: {df['week_start_date'].min()} to {df['week_start_date'].max()}")
print(f"  Number of apps: {df['app'].nunique()}")
print(f"  Number of message types: {df['message_type'].nunique()}")
print(f"  Number of weeks: {df['week_start_date'].nunique()}")
print(f"\nSample frequency distribution:")
for (app, msg_type), config in list(app_msg_config.items())[:5]:
    weeks_with_data = len(df[(df['app'] == app) & (df['message_type'] == msg_type)])
    print(f"  {app} - {msg_type}: {config['frequency']} ({weeks_with_data}/{NUM_WEEKS} weeks)")

print(f"\nFirst few records:")
print(df.head(10))
