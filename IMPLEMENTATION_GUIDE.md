# Meditation Device - Complete Implementation Guide

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    EEG Sensor Hardware                       │
│           (6-channel, 256Hz sampling rate)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              eeg_heartbeat_generator.py                      │
│      (Generate/Collect Raw EEG & Heart Rate Data)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    QuestDB (instance-1)                      │
│  ┌──────────────────┐    ┌─────────────────┐              │
│  │   eeg_data       │    │ heart_rate_data │              │
│  │  (raw 256Hz)     │    │ (RR intervals)  │              │
│  └──────────────────┘    └─────────────────┘              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           eeg_processor_questdb.py                           │
│     (Real-time Preprocessing & Feature Extraction)          │
│  ┌─ Referencing (CAR)                                       │
│  ├─ Filtering (Notch + Bandpass)                            │
│  ├─ Artifact Detection & Removal                            │
│  ├─ Segmentation & Normalization                            │
│  ├─ PSD & Band Power Computation                            │
│  └─ Feature Extraction (Ratios, Scores)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  eeg_processed Table                         │
│  (Processed Metrics with Timestamps)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│            realtime_monitor.py                              │
│  (Continuous Monitoring & Alert System)                    │
│  ┌─ State Classification                                    │
│  ├─ Trend Analysis                                          │
│  ├─ Alert Generation                                        │
│  └─ Session Logging                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           User Dashboard & Notifications                    │
│  (Web UI, Mobile App, Feedback to User)                    │
└─────────────────────────────────────────────────────────────┘
```

## Installation & Setup

### 1. System Requirements

```bash
Python 3.8+
RAM: 4GB minimum (8GB recommended)
Storage: 100MB for code + database space
OS: Linux/macOS/Windows
```

### 2. Install Dependencies

```bash
# Core dependencies
pip install numpy pandas scipy psycopg2-binary

# Optional visualization
pip install matplotlib plotly

# For advanced features
pip install pandas-profiling
```

### 3. Setup QuestDB

#### Option A: Docker
```bash
docker run -p 8812:8812 questdb/questdb
```

#### Option B: Direct Installation
```bash
# Download from https://questdb.io/get-questdb/
./questdb.sh start
```

#### Create Tables
```bash
python config_and_testing.py
# Then execute the SQL output in QuestDB
```

## Workflow

### Phase 1: Data Collection
```python
from eeg_heartbeat_generator import MeditationMetricsGenerator

# Generate test data or connect to real hardware
generator = MeditationMetricsGenerator(
    duration_seconds=300,
    eeg_sampling_rate=256,
    meditation_state='relaxed'
)

eeg_data, hr_data = generator.generate_all_metrics()
generator.save_to_csv(eeg_data, hr_data)

# Insert into QuestDB
```

### Phase 2: Real-Time Processing
```python
from eeg_processor_questdb import MeditationProcessor

processor = MeditationProcessor()
processor.process_real_time(minutes=5)
```

### Phase 3: Continuous Monitoring
```python
from realtime_monitor import RealtimeMetricsMonitor

monitor = RealtimeMetricsMonitor(
    check_interval=60,
    data_window=5
)
monitor.run_continuous_monitoring(duration_minutes=None)
```

## File Descriptions

| File | Purpose | Type |
|------|---------|------|
| `eeg_heartbeat_generator.py` | Generate synthetic EEG & HR data | Generator |
| `eeg_processor_questdb.py` | Preprocessing & feature extraction | Processor |
| `realtime_monitor.py` | Continuous monitoring & alerts | Monitor |
| `config_and_testing.py` | Configuration & testing utilities | Config |
| `EEG_PROCESSOR_README.md` | Technical documentation | Docs |
| `IMPLEMENTATION_GUIDE.md` | This file | Guide |

## Key Features Explained

### 1. EEG Referencing
**What**: Common Average Reference (CAR)
**Why**: Removes common noise and improves SNR
**How**: Subtracts mean of all channels from each channel

```
Raw Signal:     [Fp1, Fp2, Fz, Pz, O1, O2]
Average:        (Fp1+Fp2+Fz+Pz+O1+O2)/6
Referenced:     [Fp1-Avg, Fp2-Avg, ..., O2-Avg]
```

### 2. Heartbeat Artifact Detection
**What**: Uses synchronized heart rate data
**Why**: Heartbeats cause muscle artifacts in EEG
**How**: Marks ±50ms windows around each detected beat

```
HR Data:   B1------B2------B3------B4
           ↓       ↓       ↓       ↓
EEG Mark:  XX      XX      XX      XX  (X = artifact)
Result:    Clean segments preserved for analysis
```

### 3. Band Power Ratios
**Alpha/Beta**: Higher = more relaxed, better meditation
**Theta/Alpha**: Indicator of drowsiness
**Beta/Theta**: Activity level metric
**Theta/Beta**: Lower = more active, higher = more relaxed

### 4. Meditation Score
```
Score = (Alpha + Theta) / Beta
Normalized to 0-1 range

Interpretation:
  > 0.75: Excellent meditation (deep state)
  0.5-0.75: Good meditation (relaxed)
  0.3-0.5: Fair meditation (moderate)
  < 0.3: Stressed/active state
```

## Configuration

### Modify Preprocessing Parameters

```python
# In config_and_testing.py
class Config:
    PREPROCESSING = {
        'notch_filter': {
            'frequency': 60,  # Use 60Hz for US, 50Hz for others
            'quality': 30
        },
        'bandpass_filter': {
            'low_freq': 0.5,
            'high_freq': 100,
            'order': 4
        }
    }
```

### Adjust Segmentation

```python
SEGMENTATION = {
    'segment_duration': 5,    # Change to 10 for longer windows
    'overlap_ratio': 0.5      # Change to 0.75 for more overlap
}
```

### Set Alert Thresholds

```python
thresholds = {
    'excellent_meditation': 0.75,
    'good_meditation': 0.55,
    'fair_meditation': 0.35,
    'stress_alert': 0.25
}
```

## Database Queries

### Check Raw EEG Data
```sql
SELECT 
    timestamp,
    fp1, fp2, fz, pz, o1, o2
FROM eeg_data
WHERE timestamp > now() - 5m
LIMIT 100;
```

### Get Processed Features
```sql
SELECT 
    timestamp,
    meditation_score,
    alpha_beta_ratio,
    theta_alpha_ratio,
    quality_state
FROM eeg_processed
WHERE timestamp > now() - 1h
ORDER BY timestamp DESC;
```

### Calculate Session Statistics
```sql
SELECT
    session_id,
    COUNT(*) as segments,
    AVG(meditation_score) as avg_score,
    MAX(meditation_score) as peak_score,
    MIN(meditation_score) as min_score
FROM eeg_processed
GROUP BY session_id
ORDER BY timestamp DESC;
```

### Find Best Meditation Periods
```sql
SELECT
    timestamp,
    meditation_score,
    alpha_beta_ratio
FROM eeg_processed
WHERE meditation_score > 0.75
AND timestamp > now() - 7d
ORDER BY meditation_score DESC;
```

## Troubleshooting

### Issue: "Connection refused" Error
```
Solution:
1. Check QuestDB is running: docker ps
2. Verify port: 8812
3. Test connection: python -c "import psycopg2; psycopg2.connect(...)"
```

### Issue: No Data in Database
```
Solution:
1. Verify data is being inserted
2. Check table exists: SELECT * FROM eeg_data LIMIT 1;
3. Check timestamps are recent: SELECT MAX(timestamp) FROM eeg_data;
```

### Issue: Artifact Detection Not Working
```
Solution:
1. Ensure heart_rate_data table is populated
2. Check timestamp alignment between tables
3. Verify RR intervals are in valid range (300-1500 ms)
```

### Issue: High Artifact Percentage
```
Solution:
1. Increase artifact_window from 0.05 to 0.1 seconds
2. Check for poor electrode contact
3. Reduce muscle movement during measurement
4. Check for electromagnetic interference
```

## Performance Optimization

### For Large Datasets
```python
# Process in batches
for i in range(0, total_minutes, 5):
    processor.process_real_time(minutes=5)
    time.sleep(60)  # Cool-down period
```

### For Memory Efficiency
```python
# Process and immediately save to database
# Don't keep all data in memory
for segment in segments:
    features = preprocessor.extract_features(segment)
    db.update_processed_data(features)
    del segment  # Free memory
```

### For Faster Processing
```python
# Use numpy vectorization
# Reduce segment size
# Use GPU if available (future enhancement)
```

## Data Privacy & Security

### Secure Database Access
```python
# Use environment variables
import os
host = os.getenv('QUESTDB_HOST', 'localhost')
password = os.getenv('QUESTDB_PASSWORD')
```

### Anonymize Sessions
```python
import hashlib
user_id = hashlib.sha256(user_email.encode()).hexdigest()
session_id = f"anon_{user_id}_{timestamp}"
```

### Data Retention
```sql
-- Delete data older than 30 days
DELETE FROM eeg_data WHERE timestamp < now() - 30d;
DELETE FROM eeg_processed WHERE timestamp < now() - 30d;
```

## Monitoring & Alerts

### Email Notifications
```python
import smtplib

def send_alert_email(meditation_score):
    if meditation_score > 0.8:
        # Send congratulation email
        smtp.sendmail("system@meditation.device",
                     "user@example.com",
                     "Great meditation session!")
```

### Slack Integration
```python
import requests

def send_slack_alert(message):
    requests.post(SLACK_WEBHOOK, json={'text': message})
```

### Dashboard Integration
```python
# Export to JSON for web dashboard
export_data = {
    'current_score': meditation_score,
    'trend': trend,
    'session_duration': elapsed_time,
    'timestamp': datetime.now().isoformat()
}
# Send to REST API
```

## Advanced Features

### Trend Analysis
```python
# Calculate rolling average
rolling_score = pd.Series(scores).rolling(window=5).mean()

# Detect meditation improvement
if rolling_score[-1] > rolling_score[0]:
    print("Meditation improving over time!")
```

### Biofeedback Integration
```python
# Real-time feedback to user
if meditation_score > 0.7:
    play_positive_sound()
    display_congratulations()
else:
    provide_guidance()
```

### Machine Learning (Future)
```python
# Predict meditation state transitions
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier()
model.fit(features, meditation_states)
predicted_state = model.predict(new_features)
```

## Maintenance Checklist

- [ ] Monitor database size
- [ ] Backup processed data regularly
- [ ] Validate data quality metrics
- [ ] Check for error rates in logs
- [ ] Update filter parameters if needed
- [ ] Verify electrode contacts monthly
- [ ] Calibrate sensors periodically
- [ ] Review meditation score distributions

## References & Resources

### EEG Signal Processing
- Niedermeyer & Da Silva: "Electroencephalography"
- Cohen: "EEG Analysis and Interpretation"

### Time Series Databases
- QuestDB Documentation: https://questdb.io/docs/
- PostgreSQL Wire Protocol: https://www.postgresql.org/

### Signal Processing
- Scipy Signal Processing: https://docs.scipy.org/doc/scipy/reference/signal.html
- Welch's Method: https://en.wikipedia.org/wiki/Welch%27s_method

### Meditation Research
- Britton et al. (2017): "Appraising the Current State of Neurobiological Research on Meditation"
- Goleman & Davidson (2017): "Altered Traits: Science Reveals How Meditation Changes Your Mind"

## Support & Contributing

For issues:
1. Check logs in `meditation_monitor.log`
2. Enable debug logging in `config_and_testing.py`
3. Verify data format matches specifications
4. Test with synthetic data first

## License

MIT License - Use freely for research and commercial purposes

---

**Last Updated**: 2024
**Version**: 1.0
**Status**: Production Ready
