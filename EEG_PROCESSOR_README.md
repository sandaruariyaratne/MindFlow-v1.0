# EEG Real-Time Processor with QuestDB Integration

A comprehensive Python application for processing EEG data in real-time, including preprocessing, feature extraction, and database updates. Designed for meditation measuring devices.

## Features

### 1. **Data Acquisition**
- Fetches last N minutes of EEG data from QuestDB (instance-1)
- Retrieves synchronized heart rate data for artifact detection
- Supports 6 EEG channels: Fp1, Fp2, Fz, Pz, O1, O2

### 2. **Preprocessing Pipeline**

#### Common Average Reference (CAR)
- Subtracts the average voltage across all channels from each channel
- Reduces common noise and external electromagnetic interference
- Improves signal-to-noise ratio

#### Filtering
- **Notch Filter**: Removes powerline noise (50/60 Hz)
- **Bandpass Filter**: Preserves relevant brain signals (0.5-100 Hz)
- Butterworth filter with 4th order
- Uses forward-backward filtering (filtfilt) to avoid phase distortion

#### Heartbeat Artifact Removal
- Detects heartbeat artifacts using synchronized heart rate data
- Marks artifact windows (±50ms around each beat)
- Removes contaminated EEG segments
- Reports artifact percentage

### 3. **Signal Segmentation**
- Divides continuous EEG into overlapping windows
- Default: 5-second segments with 50% overlap
- Reduces edge effects and improves feature stability

### 4. **Normalization**
- Z-score normalization (zero mean, unit variance)
- Applied per-segment for consistent feature extraction

### 5. **Feature Extraction**

#### Power Spectral Density (PSD)
- Computed using Welch's method
- Provides frequency-domain representation
- Extracted for each channel and overall

#### Brain Wave Bands
- **Delta** (0.5-4 Hz): Sleep, deep relaxation
- **Theta** (4-8 Hz): Meditation, creativity, drowsiness
- **Alpha** (8-12 Hz): Relaxation, calmness, meditation
- **Beta** (12-30 Hz): Active thinking, alertness, stress
- **Gamma** (30-100 Hz): Cognitive processing, attention

#### Power Ratios
- **Alpha/Beta**: High ratio indicates relaxation (meditation desirable)
- **Theta/Alpha**: High ratio may indicate drowsiness
- **Beta/Theta**: Indicates mental activity vs relaxation
- **Theta/Beta**: Relaxation indicator (higher = more relaxed)

#### Meditation Score
- Composite metric: (Alpha + Theta) / Beta
- Normalized to 0-1 range
- Higher score = deeper meditation state
- **>0.7**: Excellent meditation
- **0.5-0.7**: Good meditation
- **0.3-0.5**: Fair meditation
- **<0.3**: Active/stressed state

### 6. **Real-Time Database Updates**
- Creates `eeg_processed` table automatically
- Stores all extracted metrics
- Includes session tracking
- Timestamp-indexed for efficient queries

## Installation

### Requirements
```bash
pip install numpy pandas scipy psycopg2-binary
```

### Setup
1. Ensure QuestDB is running and accessible at `localhost:8812`
2. Verify `eeg_data` table exists with EEG channels
3. Verify `heart_rate_data` table exists with RR intervals

## Usage

### Basic Usage
```python
from eeg_processor_questdb import MeditationProcessor

# Initialize processor
processor = MeditationProcessor(
    questdb_host='localhost',
    questdb_port=8812
)

# Process last 5 minutes of data
processor.process_real_time(minutes=5)
```

### Advanced Usage
```python
from eeg_processor_questdb import (
    QuestDBConnector,
    EEGPreprocessor,
    MeditationProcessor
)

# Custom preprocessing
preprocessor = EEGPreprocessor(sampling_rate=256)

# Fetch data
db = QuestDBConnector()
eeg_data = db.fetch_last_n_minutes(minutes=5)
hr_data = db.fetch_heart_rate_data(minutes=5)

# Process
processed_features = preprocessor.process_eeg_data(eeg_data, hr_data)

# Update database
for features in processed_features:
    db.update_processed_data(data_dict=features)

db.close()
```

### Command Line Usage
```bash
python eeg_processor_questdb.py
```

## Output

The processor generates two types of outputs:

### 1. Console Summary
```
============================================================
MEDITATION ANALYSIS SUMMARY
============================================================

Segments Processed: 12

--- Brain Wave Power Averages ---
Theta Power:  45.23
Alpha Power:  67.89
Beta Power:   34.12
Gamma Power:  8.45

--- Frequency Ratios ---
Alpha/Beta Ratio:   1.9876
Theta/Alpha Ratio:  0.6672
Beta/Theta Ratio:   0.7550
Theta/Beta Ratio:   1.3254

--- Meditation Quality ---
Meditation Score: 85.34%
Quality Assessment: EXCELLENT - Deep meditation state
============================================================
```

### 2. Database Updates
Creates `eeg_processed` table with:
- **timestamp**: Segment timestamp
- **session_id**: Unique session identifier
- **segment_number**: Segment index
- **fp1_psd to o2_psd**: Per-channel PSD values
- **alpha_power, beta_power, theta_power, gamma_power**: Band power values
- **alpha_beta_ratio, theta_alpha_ratio, beta_theta_ratio, theta_beta_ratio**: Frequency ratios
- **meditation_score**: Composite meditation quality metric
- **processed_at**: Processing timestamp

## Database Schema

### eeg_processed Table
```sql
CREATE TABLE eeg_processed (
    timestamp TIMESTAMP,
    session_id STRING,
    segment_number INT,
    fp1_psd DOUBLE,
    fp2_psd DOUBLE,
    fz_psd DOUBLE,
    pz_psd DOUBLE,
    o1_psd DOUBLE,
    o2_psd DOUBLE,
    alpha_power DOUBLE,
    beta_power DOUBLE,
    theta_power DOUBLE,
    gamma_power DOUBLE,
    alpha_beta_ratio DOUBLE,
    theta_alpha_ratio DOUBLE,
    beta_theta_ratio DOUBLE,
    theta_beta_ratio DOUBLE,
    meditation_score DOUBLE,
    processed_at TIMESTAMP
) timestamp(timestamp);
```

## API Reference

### MeditationProcessor
```python
processor = MeditationProcessor(questdb_host, questdb_port)
processor.process_real_time(minutes=5)
```

### EEGPreprocessor
```python
preprocessor = EEGPreprocessor(sampling_rate=256)
processed_data = preprocessor.process_eeg_data(eeg_df, hr_df)
```

### QuestDBConnector
```python
db = QuestDBConnector(host, port, user, password)
eeg_data = db.fetch_last_n_minutes(table_name, minutes, eeg_channels)
hr_data = db.fetch_heart_rate_data(table_name, minutes)
db.update_processed_data(table_name, data_dict)
db.close()
```

## Processing Steps Explained

1. **Referencing**: Remove common noise by subtracting channel average
2. **Notch Filtering**: Remove 50Hz powerline interference
3. **Bandpass Filtering**: Keep only relevant brain signals (0.5-100 Hz)
4. **Artifact Detection**: Identify and mark heartbeat-related artifacts
5. **Artifact Removal**: Remove contaminated segments
6. **Segmentation**: Divide into overlapping 5-second windows
7. **Normalization**: Standardize each segment (z-score)
8. **PSD Computation**: Calculate power spectrum for each segment
9. **Band Power Extraction**: Compute power in each frequency band
10. **Ratio Calculation**: Calculate band power ratios
11. **Meditation Scoring**: Generate composite meditation quality score
12. **Database Update**: Store all metrics with timestamp

## Performance Considerations

- **Memory**: ~50MB for 5 minutes of 6-channel 256Hz data
- **Processing Time**: ~500ms for 5-minute session (varies with hardware)
- **Database Throughput**: 1-2 updates per second
- **Segment Count**: ~60 segments for 5-minute session (5s segments, 50% overlap)

## Troubleshooting

### Connection Issues
```python
# Check QuestDB connection
try:
    db = QuestDBConnector()
    print("Connected successfully")
except Exception as e:
    print(f"Connection failed: {e}")
```

### No Data
- Verify tables exist: `eeg_data` and `heart_rate_data`
- Check data is being inserted
- Verify timestamps are recent

### Artifacts
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | >=1.20 | Numerical computing |
| pandas | >=1.3 | Data manipulation |
| scipy | >=1.7 | Signal processing |
| psycopg2 | >=2.9 | QuestDB connection |

## License
MIT License

## References

1. Siegel, A., & Sapru, H. N. (2006). Essential Neuroscience
2. Niedermeyer, E., & Da Silva, F. L. (2004). Electroencephalography
3. Cummins, T. D., & Lithari, C. (2014). Spectral Characterization of Brain Frequency Ranges
4. Klimesch, W., et al. (2007). EEG alpha oscillations as a tool for studying attention

## Support

For issues or questions:
1. Check logs for error messages
2. Verify database connectivity
3. Ensure data format matches specifications
4. Review preprocessing parameters
