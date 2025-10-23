# Payment Screening Volume Monitoring & Alerting System

## Overview

This system provides automated volume monitoring and alerting for payment screening systems that process SWIFT and non-SWIFT messages from multiple sources with variable frequencies.

### Key Features

✅ **Dynamic Threshold Calculation** - Automatically calculates thresholds based on historical patterns
✅ **Multi-Frequency Support** - Handles daily, weekly, monthly, quarterly, and semi-annual message patterns
✅ **Statistical Rigor** - Uses multiple statistical methods (Z-score, Percentile, IQR)
✅ **Configurable Sensitivity** - Three sensitivity levels (High, Medium, Low)
✅ **Comprehensive Alerting** - Prioritized alerts (CRITICAL, HIGH, MEDIUM, LOW)
✅ **Production Ready** - Designed for weekly Monday morning execution

---

## System Architecture

```
payment_screening_volumes.csv
    ↓
volume_analysis.py → Analyzes historical data
    ↓                Calculates thresholds
    ↓                Detects frequencies
    ↓
threshold_configuration.csv
    ↓
weekly_monitoring.py → Runs every Monday
    ↓                   Checks last week's volume
    ↓                   Compares vs thresholds
    ↓
Alerts Generated → CSV / JSON / Email
```

---

## Files Description

### Data Files
- `payment_screening_volumes.csv` - Historical volume data (2 years, weekly)
- `generate_data.py` - Generates realistic test data

### Analysis Scripts
- `volume_analysis.py` - Full analysis with threshold calculation
- `create_visualizations.py` - Generates 8 presentation-ready charts
- `weekly_monitoring.py` - Production monitoring script

### Output Files
- `analysis_output/threshold_configuration.csv` - Calculated thresholds
- `analysis_output/alerts_YYYYMMDD.csv` - Weekly alerts in CSV format
- `analysis_output/alerts_YYYYMMDD.json` - Weekly alerts in JSON format
- `analysis_output/report_YYYYMMDD.txt` - Formatted text report
- `analysis_output/*.png` - Visualization charts

---

## Quick Start

### 1. Initial Analysis (One-time setup)

```bash
# Analyze historical data and calculate thresholds
python3 volume_analysis.py

# Generate visualizations for presentation
python3 create_visualizations.py
```

### 2. Weekly Monitoring (Run every Monday)

```bash
# Run with default settings (medium sensitivity)
python3 weekly_monitoring.py

# Run with custom sensitivity
python3 weekly_monitoring.py --sensitivity high

# Check a specific date
python3 weekly_monitoring.py --date 2025-10-20

# Custom output directory
python3 weekly_monitoring.py --output-dir /path/to/alerts
```

---

## Threshold Methodology

The system uses **multiple statistical methods** and takes the **most conservative** (highest) threshold:

### Method 1: Z-Score Based
```
Threshold = Mean - (Z × Standard Deviation)
```
- High sensitivity: Z = 1.5
- Medium sensitivity: Z = 2.0
- Low sensitivity: Z = 2.5

### Method 2: Percentile Based
```
Threshold = Xth Percentile of historical volumes
```
- High sensitivity: 10th percentile
- Medium sensitivity: 5th percentile
- Low sensitivity: 2nd percentile

### Method 3: IQR Based
```
Threshold = Q1 - (1.5 × IQR)
```
- Robust to outliers
- Standard box-plot method

### Final Threshold
```
Threshold = MAX(Z-Score Method, Percentile Method, IQR Method)
```

This ensures we use the most conservative threshold, reducing false positives.

---

## Alert Severity Levels

| Severity | Drop from Mean | Action Required |
|----------|---------------|-----------------|
| **CRITICAL** | ≥ 70% | Immediate investigation - possible system failure |
| **HIGH** | 50-69% | Urgent review - significant drop |
| **MEDIUM** | 30-49% | Review within 24 hours |
| **LOW** | < 30% | Monitor - minor variance |

Special alert type:
- **NO_DATA**: No messages received this week (automatically CRITICAL)

---

## Sensitivity Configuration

### High Sensitivity
- **Use when**: You need to catch small variations
- **Z-score**: 1.5 (more sensitive)
- **Percentile**: 10th
- **Min weeks**: 4
- **Result**: More alerts, fewer missed drops
- **Best for**: Critical message types, regulatory messages

### Medium Sensitivity (Recommended)
- **Use when**: Standard monitoring
- **Z-score**: 2.0 (balanced)
- **Percentile**: 5th
- **Min weeks**: 6
- **Result**: Balanced alert rate
- **Best for**: Most message types, general monitoring

### Low Sensitivity
- **Use when**: You want only significant drops
- **Z-score**: 2.5 (less sensitive)
- **Percentile**: 2nd
- **Min weeks**: 8
- **Result**: Fewer alerts, only major drops
- **Best for**: High-variability message types

---

## Data Requirements

### Input CSV Format
```csv
app,message_type,week_start_date,volume
APP_01,MT103,2023-10-30,1500000
APP_01,MT103,2023-11-06,1520000
...
```

### Fields
- `app`: System/application name (e.g., APP_01, APP_02, ...)
- `message_type`: Message type code (e.g., MT103, MX234, CUSTOM_001)
- `week_start_date`: Monday date in YYYY-MM-DD format
- `volume`: Number of messages processed that week

### Data Expectations
- **Frequency**: Weekly snapshots (every Monday)
- **History**: Minimum 2 years recommended
- **Volume range**: 300 to 20 million per week
- **Consistency**: Every Monday without gaps

---

## Automated Scheduling

### Cron Job (Linux/Mac)

Add to crontab:
```bash
# Run every Monday at 6 AM
0 6 * * 1 /usr/bin/python3 /path/to/weekly_monitoring.py --sensitivity medium >> /path/to/logs/monitoring.log 2>&1
```

### Windows Task Scheduler
- Create a scheduled task
- Trigger: Weekly, every Monday at 6:00 AM
- Action: Run `python3 weekly_monitoring.py --sensitivity medium`

---

## Interpreting Results

### Sample Alert Output

```
================================================================================
PAYMENT SCREENING VOLUME ALERT REPORT
================================================================================
Week Starting: 2025-10-20
Sensitivity Level: MEDIUM

ALERT SUMMARY:
  Total Alerts: 50
  CRITICAL  : 5
  HIGH      : 23
  MEDIUM    : 8
  LOW       : 14

--------------------------------------------------------------------------------
HIGH PRIORITY ALERTS (23)
--------------------------------------------------------------------------------

App: APP_01 | Message Type: MT924
  Current Volume: 2,167,569
  Threshold: 7,473,483
  Mean Volume: 10,000,000
  Recent 4-Week Avg: 9,800,000
  Drop from Mean: 77.4%
  Message: Volume dropped 77.4% below historical mean
```

### What to do with alerts:

1. **CRITICAL Alerts (NO_DATA)**
   - Check if the system is running
   - Verify connectivity
   - Check for maintenance windows
   - Contact system administrator immediately

2. **CRITICAL/HIGH Alerts (Large drops)**
   - Verify with business teams
   - Check for holiday/weekend effects
   - Review system logs
   - Investigate potential issues

3. **MEDIUM Alerts**
   - Monitor trend over next few weeks
   - Document if expected (e.g., month-end effects)
   - Keep stakeholders informed

4. **LOW Alerts**
   - Normal variance
   - Track but no immediate action needed

---

## Visualization Outputs

The `create_visualizations.py` script generates 8 presentation-ready charts:

1. **01_overall_trends.png** - Total volume trends, top apps, volume distribution
2. **02_frequency_distribution.png** - Message frequency categories analysis
3. **03_threshold_examples.png** - Example trends with calculated thresholds
4. **04_app_summary.png** - App-level performance metrics
5. **05_message_type_analysis.png** - Message type deep dive
6. **06_threshold_methodology.png** - Threshold calculation comparisons
7. **07_temporal_patterns.png** - Seasonal and monthly patterns
8. **08_executive_summary.png** - Executive dashboard with key metrics

All charts are high-resolution (300 DPI) and presentation-ready.

---

## Customization

### Adjusting Thresholds

Edit `weekly_monitoring.py`:

```python
SENSITIVITY_CONFIGS = {
    'custom': {
        'z_score': 1.8,        # Adjust this
        'percentile': 7,       # Adjust this
        'min_weeks': 5,        # Minimum data required
        'description': 'Custom sensitivity'
    }
}
```

### Adding Email Notifications

Add to `weekly_monitoring.py` after alert generation:

```python
import smtplib
from email.mime.text import MIMEText

def send_email_alert(alerts_df, check_date):
    if len(alerts_df) == 0:
        return

    msg = MIMEText(report)
    msg['Subject'] = f'Payment Screening Alerts - {check_date}'
    msg['From'] = 'monitoring@company.com'
    msg['To'] = 'team@company.com'

    smtp = smtplib.SMTP('smtp.company.com', 587)
    smtp.send_message(msg)
    smtp.quit()

# Call after generating report
send_email_alert(alerts_df, check_date)
```

---

## Troubleshooting

### Issue: Too many alerts

**Solution**: Lower sensitivity
```bash
python3 weekly_monitoring.py --sensitivity low
```

### Issue: Missing expected alerts

**Solution**: Increase sensitivity
```bash
python3 weekly_monitoring.py --sensitivity high
```

### Issue: No data for specific week

**Check**:
- Is the data file updated?
- Is the date correct (should be Monday)?
- Run with `--date` parameter to specify exact week

### Issue: Threshold too low/high

**Solution**: Adjust sensitivity or recalculate with more historical data

---

## Performance Metrics

### Test Dataset
- 26 apps
- 332 message types
- 1,147 app-message combinations
- 99,398 total weekly records
- 508 billion messages processed

### Processing Time
- Analysis: ~5 seconds
- Visualization: ~30 seconds
- Weekly monitoring: <2 seconds

### Memory Usage
- Data loading: ~50 MB
- Analysis: ~100 MB
- Visualization: ~200 MB

---

## Recommendations

### Immediate (Week 1)
1. ✅ Run initial analysis on historical data
2. ✅ Generate visualizations for stakeholder presentation
3. ✅ Review threshold configurations
4. ✅ Set up weekly monitoring with medium sensitivity

### Short-term (Month 1)
1. Fine-tune sensitivity based on alert feedback
2. Integrate with email/Slack notifications
3. Set up automated Monday morning runs (cron/scheduler)
4. Create dashboard integration (Tableau/PowerBI)

### Long-term (Quarter 1)
1. Machine learning-based anomaly detection
2. Predictive volume forecasting
3. Trend analysis for capacity planning
4. Integration with incident management system

---

## Support & Contact

For issues or questions:
1. Review the troubleshooting section
2. Check alert report for detailed messages
3. Contact: [Your contact information]

---

## Version History

**v1.0** - Initial release
- Dynamic threshold calculation
- Multi-frequency support
- Three sensitivity levels
- Comprehensive alerting
- Production-ready monitoring script

---

## License

[Your license information]

---

**Last Updated**: October 2025
