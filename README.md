# Meditation Device - Complete File Index & Quick Reference

## 📁 Project Structure

```
meditation-device/
├── eeg_heartbeat_generator.py          # (340 lines) Data generation
├── eeg_processor_questdb.py            # (674 lines) Core processing
├── realtime_monitor.py                 # (372 lines) Monitoring system
├── config_and_testing.py               # (403 lines) Configuration
├── EEG_PROCESSOR_README.md             # Technical documentation
├── IMPLEMENTATION_GUIDE.md             # Deployment guide
└── README.md                           # This file
```

## 📊 Files Overview

### 1. **eeg_heartbeat_generator.py** (340 lines)
**Purpose**: Generate synthetic EEG and heart rate data

**Key Classes**:
- `MeditationMetricsGenerator` - Main generator class

**Key Methods**:
```python
generator = MeditationMetricsGenerator(
    duration_seconds=300,
    meditation_state='relaxed'
)
eeg_df, hr_df = generator.generate_all_metrics()
generator.save_to_csv(eeg_df, hr_df)
```

**Output**:
- `eeg_data.csv` - 6 EEG channels at 256Hz
- `heart_rate_data.csv` - RR intervals + BPM

**Use Case**: Generate test data, prototype testing, benchmarking

---

### 2. **eeg_processor_questdb.py** (674 lines) ⭐ MAIN FILE
**Purpose**: Real-time EEG preprocessing and feature extraction

**Key Classes**:
- `QuestDBConnector` - Database operations
- `EEGPreprocessor` - Signal processing pipeline
- `MeditationProcessor` - Main orchestrator

**Processing Pipeline**:
```
1. Referencing (CAR)
   ↓
2. Filtering (Notch + Bandpass)
   ↓
3. Heartbeat Artifact Detection
   ↓
4. Artifact Removal
   ↓
5. Segmentation
   ↓
6. Normalization
   ↓
7. PSD Computation
   ↓
8. Feature Extraction
   ↓
9. Database Update
```

**Key Methods**:
```python
processor = MeditationProcessor()
processor.process_real_time(minutes=5)

# Or use components separately
db = QuestDBConnector()
eeg_data = db.fetch_last_n_minutes(minutes=5)
hr_data = db.fetch_heart_rate_data(minutes=5)

preprocessor = EEGPreprocessor()
features = preprocessor.process_eeg_data(eeg_data, hr_data)
```

**Output Metrics**:
- Per-channel PSD values
- Band powers: Theta, Alpha, Beta, Gamma
- Ratios: Alpha/Beta, Theta/Alpha, Beta/Theta, Theta/Beta
- Meditation Score (0-1)

**Database Table**: `eeg_processed`

---

### 3. **realtime_monitor.py** (372 lines)
**Purpose**: Continuous real-time monitoring with alerts

**Key Classes**:
- `RealtimeMetricsMonitor` - Main monitoring class

**Features**:
- Continuous data fetching and processing
- State classification (Excellent/Good/Fair/Alert/Stress)
- Real-time dashboard display
- Trend analysis
- Alert generation and logging
- Session summary saving

**Key Methods**:
```python
monitor = RealtimeMetricsMonitor(
    check_interval=60,      # Process every 60s
    data_window=5,          # 5-minute data window
    history_size=100        # Keep 100 samples
)
monitor.run_continuous_monitoring(duration_minutes=30)
```

**Output**:
- Console dashboard every cycle
- Alert logs: `alerts_<session_id>.log`
- Session summary: `session_<session_id>_summary.json`

**State Mapping**:
| Meditation Score | State | Description |
|---|---|---|
| > 0.75 | Excellent | Deep meditation |
| 0.55-0.75 | Good | Relaxed meditation |
| 0.35-0.55 | Fair | Moderate meditation |
| 0.25-0.35 | Alert | Active/Focused |
| < 0.25 | Stress | Stressed state |

---

### 4. **config_and_testing.py** (403 lines)
**Purpose**: Configuration, setup, and testing utilities

**Key Classes**:
- `Config` - Centralized configuration
- `TestDataGenerator` - Data generation utilities
- `DataValidator` - Data validation tools

**Configuration Sections**:
```python
Config.QUESTDB          # Database settings
Config.EEG              # EEG parameters
Config.PREPROCESSING    # Filter settings
Config.SEGMENTATION     # Window settings
Config.FREQUENCY_BANDS  # Band definitions
Config.LOGGING          # Log configuration
```

**Key Functions**:
```python
# Save/load configuration
TestDataGenerator.save_config_to_file('config.json')
config = TestDataGenerator.load_config_from_file()

# Validate data
validator = DataValidator()
eeg_valid = validator.validate_eeg_data(df)
hr_valid = validator.validate_heart_rate_data(df)

# Database setup
print(QUESTDB_SETUP_SQL)  # Run in QuestDB admin
```

**Output**: `config.json`, database setup SQL

---

### 5. **EEG_PROCESSOR_README.md** (296 lines)
**Purpose**: Technical documentation for the processing system

**Sections**:
- Features overview
- Installation instructions
- Preprocessing pipeline explanation
- Feature extraction details
- Database schema
- API reference
- Troubleshooting guide

**When to Read**: Before implementation, understand the architecture

---

### 6. **IMPLEMENTATION_GUIDE.md** (483 lines)
**Purpose**: Complete deployment and operational guide

**Sections**:
- System architecture diagram
- Installation steps
- Workflow phases
- Configuration customization
- Database queries
- Troubleshooting procedures
- Performance optimization
- Security best practices
- Maintenance checklist

**When to Read**: During deployment, operational setup

---

## 🚀 Quick Start

### 1. Setup (5 minutes)
```bash
# Install dependencies
pip install numpy pandas scipy psycopg2-binary

# Start QuestDB
docker run -p 8812:8812 questdb/questdb

# Create tables
python config_and_testing.py
```

### 2. Generate Data (1 minute)
```python
from eeg_heartbeat_generator import MeditationMetricsGenerator

generator = MeditationMetricsGenerator(duration_seconds=300)
eeg_df, hr_df = generator.generate_all_metrics()
generator.save_to_csv(eeg_df, hr_df)

# Insert into QuestDB manually or via API
```

### 3. Process Data (2 minutes)
```python
from eeg_processor_questdb import MeditationProcessor

processor = MeditationProcessor()
processor.process_real_time(minutes=5)
```

### 4. Monitor (Continuous)
```python
from realtime_monitor import RealtimeMetricsMonitor

monitor = RealtimeMetricsMonitor()
monitor.run_continuous_monitoring()  # Ctrl+C to stop
```

---

## 📈 Processing Features

### Signal Processing
- ✅ Common Average Reference (CAR)
- ✅ Notch filter (50/60 Hz powerline noise)
- ✅ Bandpass filter (0.5-100 Hz)
- ✅ Forward-backward filtering (no phase distortion)
- ✅ Heartbeat artifact detection & removal

### Feature Extraction
- ✅ Power Spectral Density (Welch's method)
- ✅ 5 frequency bands (Delta, Theta, Alpha, Beta, Gamma)
- ✅ Band power calculations
- ✅ 4 key ratios (Alpha/Beta, Theta/Alpha, etc.)
- ✅ Meditation quality score

### Real-Time Capabilities
- ✅ Continuous data streaming
- ✅ Real-time processing (256 Hz)
- ✅ State classification
- ✅ Alert generation
- ✅ Session tracking
- ✅ Trend analysis

---

## 🔧 Common Tasks

### Task 1: Process Last 5 Minutes
```python
from eeg_processor_questdb import MeditationProcessor
processor = MeditationProcessor()
processor.process_real_time(minutes=5)
```

### Task 2: Query Processed Data
```sql
SELECT timestamp, meditation_score, alpha_beta_ratio
FROM eeg_processed
WHERE timestamp > now() - 1h
ORDER BY timestamp DESC
LIMIT 100;
```

### Task 3: Find Best Meditation Sessions
```sql
SELECT session_id, AVG(meditation_score) as avg_score
FROM eeg_processed
WHERE meditation_score > 0.7
GROUP BY session_id
ORDER BY avg_score DESC;
```

### Task 4: Validate Data Quality
```python
from config_and_testing import DataValidator
validator = DataValidator()
result = validator.validate_eeg_data(eeg_df)
print(f"Valid: {result['valid']}")
print(f"Issues: {result['issues']}")
```

### Task 5: Change Processing Parameters
```python
from config_and_testing import Config

# Modify and save
Config.PREPROCESSING['bandpass_filter']['high_freq'] = 50
Config.SEGMENTATION['segment_duration'] = 10
TestDataGenerator.save_config_to_file()
```

### Task 6: Set Up Alerts
```python
# In realtime_monitor.py, modify thresholds:
monitor.thresholds = {
    'excellent_meditation': 0.8,
    'good_meditation': 0.6,
    'fair_meditation': 0.4,
    'stress_alert': 0.2
}
```

---

## 📊 Database Schema

### eeg_data (Raw)
```sql
timestamp TIMESTAMP
fp1, fp2, fz, pz, o1, o2 DOUBLE
```

### heart_rate_data (Raw)
```sql
timestamp TIMESTAMP
rr_interval_ms DOUBLE
heart_rate_bpm DOUBLE
```

### eeg_processed (Features)
```sql
timestamp TIMESTAMP
session_id STRING
segment_number INT
fp1_psd, fp2_psd, fz_psd, pz_psd, o1_psd, o2_psd DOUBLE
alpha_power, beta_power, theta_power, gamma_power DOUBLE
alpha_beta_ratio, theta_alpha_ratio, beta_theta_ratio, theta_beta_ratio DOUBLE
meditation_score DOUBLE
processed_at TIMESTAMP
```

---

## 🎯 Key Metrics Explained

| Metric | Range | Meaning |
|--------|-------|---------|
| **Meditation Score** | 0-1 | Overall meditation quality |
| **Alpha/Beta** | 0-∞ | Relaxation indicator (higher = more relaxed) |
| **Theta/Alpha** | 0-∞ | Drowsiness indicator |
| **Beta/Theta** | 0-∞ | Activity level (higher = more active) |
| **Alpha Power** | μV² | Brain relaxation state |
| **Beta Power** | μV² | Mental activity level |
| **Theta Power** | μV² | Creativity & relaxation |
| **Gamma Power** | μV² | Cognitive processing |

---

## 🐛 Troubleshooting Matrix

| Problem | Cause | Solution |
|---------|-------|----------|
| No data fetched | DB connection | Check QuestDB running, verify host:port |
| Artifact not removed | Wrong HR data | Ensure timestamps align, check RR intervals |
| Low meditation score | Device noise | Check electrode contact, reduce movement |
| Processing slow | Large dataset | Process in smaller batches, increase interval |
| High memory usage | Keeping all data | Process and discard immediately |

---

## 📚 Learning Path

1. **Day 1**: Read documentation files
   - EEG_PROCESSOR_README.md (1 hour)
   - IMPLEMENTATION_GUIDE.md (1 hour)

2. **Day 2**: Setup and basic operation
   - Install dependencies
   - Start QuestDB
   - Generate test data
   - Run basic processor

3. **Day 3**: Customize and optimize
   - Modify configuration
   - Adjust parameters
   - Deploy monitoring
   - Set up alerts

4. **Day 4+**: Advanced usage
   - Custom analysis
   - Integration with other systems
   - Performance tuning
   - Adding features

---

## 🔗 File Dependencies

```
realtime_monitor.py
    └── depends on: eeg_processor_questdb.py

eeg_processor_questdb.py
    └── depends on: (none) - standalone

config_and_testing.py
    └── depends on: (optional) used by other files

eeg_heartbeat_generator.py
    └── depends on: (none) - standalone
```

---

## 📋 Pre-Implementation Checklist

- [ ] Python 3.8+ installed
- [ ] QuestDB installed and running
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Database tables created
- [ ] Test data generated
- [ ] Configuration reviewed and customized
- [ ] QuestDB connection verified
- [ ] Initial processing test successful

---

## 🎓 Additional Resources

### Scientific References
- Klimesch et al. (2007): EEG alpha oscillations and attention
- Niedermeyer & Da Silva (2004): Electroencephalography: Basic Principles
- Cummins & Lithari (2014): Spectral Characterization of Brain Frequency Ranges

### Tools & Libraries
- Scipy Signal Processing: https://docs.scipy.org/doc/scipy/reference/signal.html
- Pandas Documentation: https://pandas.pydata.org/docs/
- QuestDB Docs: https://questdb.io/docs/

### Related Work
- MNE-Python: EEG analysis library
- Brainstorm: Brain mapping software
- EEGLAB: EEG processing toolbox

---

## 📝 Changelog

**Version 1.0** (Current)
- ✅ Full preprocessing pipeline
- ✅ QuestDB integration
- ✅ Real-time monitoring
- ✅ Feature extraction
- ✅ Artifact removal

**Planned Enhancements**
- Machine learning meditation state prediction
- GPU acceleration for processing
- Web dashboard integration
- Mobile app support
- Advanced visualization
- Multi-user session management

---

## 📧 Support

**Issues?** Check these resources in order:
1. Relevant documentation file (README or IMPLEMENTATION_GUIDE)
2. Comments in the Python file
3. Logs: `meditation_monitor.log`
4. Database: `SELECT * FROM <table> LIMIT 1`
5. Test with synthetic data from generator

---

## 📄 License

MIT License - Free for research and commercial use

---

## 🙏 Acknowledgments

Built with:
- NumPy/SciPy for signal processing
- Pandas for data manipulation
- QuestDB for time-series storage
- Python 3.8+

---

**Last Updated**: May 2, 2024
**Status**: Production Ready
**Version**: 1.0.0
**Maintainer**: Meditation Device Team

---

## 📞 Quick Reference Commands

```bash
# Install all dependencies
pip install numpy pandas scipy psycopg2-binary matplotlib

# Start QuestDB
docker run -d -p 8812:8812 questdb/questdb

# Generate test data
python eeg_heartbeat_generator.py

# Process data
python eeg_processor_questdb.py

# Monitor in real-time
python realtime_monitor.py

# Setup configuration
python config_and_testing.py

# Check logs
tail -f meditation_monitor.log
```

---

**Ready to meditate? Start with the IMPLEMENTATION_GUIDE.md! 🧘**
