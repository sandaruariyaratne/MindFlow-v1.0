"""
EEG Processor Configuration and Testing Utilities

This module provides configuration templates and testing utilities
for the EEG processor with QuestDB integration.
"""

import json
import os
from datetime import datetime

# ============================================================================
# CONFIGURATION TEMPLATES
# ============================================================================

class Config:
    """Configuration class for EEG processor."""

    # QuestDB Configuration
    QUESTDB = {
        'host': 'localhost',
        'port': 8812,
        'user': 'admin',
        'password': 'quest',
        'database': 'qdb'
    }

    # EEG Configuration
    EEG = {
        'sampling_rate': 256,  # Hz
        'channels': ['Fp1', 'Fp2', 'Fz', 'Pz', 'O1', 'O2'],
        'table_name': 'eeg_data'
    }

    # Heart Rate Configuration
    HEART_RATE = {
        'sampling_rate_hz': 1,  # Variable, based on heart rate
        'table_name': 'heart_rate_data'
    }

    # Preprocessing Configuration
    PREPROCESSING = {
        'referencing_method': 'CAR',  # Common Average Reference
        'notch_filter': {
            'frequency': 50,  # Hz (use 60 for US)
            'quality': 30
        },
        'bandpass_filter': {
            'low_freq': 0.5,  # Hz
            'high_freq': 100,  # Hz
            'order': 4
        },
        'artifact_window': 0.05  # seconds (±50ms around heartbeat)
    }

    # Segmentation Configuration
    SEGMENTATION = {
        'segment_duration': 5,  # seconds
        'overlap_ratio': 0.5  # 50% overlap
    }

    # Frequency Bands Configuration
    FREQUENCY_BANDS = {
        'delta': (0.5, 4),
        'theta': (4, 8),
        'alpha': (8, 12),
        'beta': (12, 30),
        'gamma': (30, 100)
    }

    # Processing Configuration
    PROCESSING = {
        'fetch_interval': 60,  # seconds between processing cycles
        'data_window': 5,  # minutes of data to process
        'real_time_mode': True,
        'batch_mode': False
    }

    # Output Configuration
    OUTPUT = {
        'save_csv': True,
        'save_json': False,
        'csv_output_dir': './output',
        'database_update': True,
        'processed_table_name': 'eeg_processed'
    }

    # Logging Configuration
    LOGGING = {
        'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
        'format': '%(asctime)s - %(levelname)s - %(message)s',
        'file': './logs/eeg_processor.log'
    }


# ============================================================================
# DATABASE SETUP SCRIPT
# ============================================================================

QUESTDB_SETUP_SQL = """
-- Create EEG raw data table
CREATE TABLE IF NOT EXISTS eeg_data (
    timestamp TIMESTAMP,
    fp1 DOUBLE,
    fp2 DOUBLE,
    fz DOUBLE,
    pz DOUBLE,
    o1 DOUBLE,
    o2 DOUBLE
) timestamp(timestamp);

-- Create heart rate data table
CREATE TABLE IF NOT EXISTS heart_rate_data (
    timestamp TIMESTAMP,
    rr_interval_ms DOUBLE,
    heart_rate_bpm DOUBLE
) timestamp(timestamp);

-- Create processed features table
CREATE TABLE IF NOT EXISTS eeg_processed (
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

-- Create meditation session log table
CREATE TABLE IF NOT EXISTS meditation_sessions (
    session_id STRING,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes DOUBLE,
    avg_meditation_score DOUBLE,
    quality_assessment STRING,
    notes STRING
) timestamp(start_time);
"""


# ============================================================================
# TESTING UTILITIES
# ============================================================================

class TestDataGenerator:
    """Generate test data for development."""

    @staticmethod
    def save_config_to_file(filepath='config.json'):
        """Save current configuration to JSON file."""
        config_dict = {
            'questdb': Config.QUESTDB,
            'eeg': Config.EEG,
            'heart_rate': Config.HEART_RATE,
            'preprocessing': Config.PREPROCESSING,
            'segmentation': Config.SEGMENTATION,
            'frequency_bands': Config.FREQUENCY_BANDS,
            'processing': Config.PROCESSING,
            'output': Config.OUTPUT,
            'logging': Config.LOGGING
        }

        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)

        print(f"✓ Configuration saved to {filepath}")

    @staticmethod
    def load_config_from_file(filepath='config.json'):
        """Load configuration from JSON file."""
        if not os.path.exists(filepath):
            print(f"✗ Config file not found: {filepath}")
            return None

        with open(filepath, 'r') as f:
            return json.load(f)


# ============================================================================
# QUICKSTART EXAMPLES
# ============================================================================

QUICKSTART_EXAMPLES = """
# EEG PROCESSOR QUICKSTART GUIDE

## 1. Basic Processing
```python
from eeg_processor_questdb import MeditationProcessor

processor = MeditationProcessor(
    questdb_host='localhost',
    questdb_port=8812
)
processor.process_real_time(minutes=5)
```

## 2. Custom Configuration
```python
from eeg_processor_questdb import EEGPreprocessor, QuestDBConnector
from config import Config

# Customize preprocessing
preprocessor = EEGPreprocessor(sampling_rate=Config.EEG['sampling_rate'])

# Fetch data with custom parameters
db = QuestDBConnector(**Config.QUESTDB)
eeg_data = db.fetch_last_n_minutes(
    table_name=Config.EEG['table_name'],
    minutes=5
)
```

## 3. Batch Processing
```python
processor = MeditationProcessor()

# Process multiple sessions
for i in range(10):
    processor.process_real_time(minutes=5)
    print(f"Session {i+1}/10 complete")
```

## 4. Data Analysis
```python
import pandas as pd

# Query processed data
db = QuestDBConnector()
query = '''
SELECT 
    timestamp,
    meditation_score,
    alpha_beta_ratio,
    theta_alpha_ratio
FROM eeg_processed
WHERE timestamp > now() - 1h
ORDER BY timestamp
'''
# Use your preferred query method
```

## 5. Real-Time Monitoring
```python
import time
from datetime import datetime

processor = MeditationProcessor()

print("Starting real-time monitoring (Ctrl+C to stop)...")
try:
    while True:
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] Processing data...")
        processor.process_real_time(minutes=5)
        time.sleep(60)  # Process every 60 seconds
except KeyboardInterrupt:
    print("\\nMonitoring stopped")
```

## 6. Feature Visualization
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load processed data
db = QuestDBConnector()
processed_df = pd.read_sql(
    "SELECT * FROM eeg_processed ORDER BY timestamp",
    db.conn
)

# Plot meditation score over time
plt.figure(figsize=(12, 6))
plt.plot(processed_df['timestamp'], processed_df['meditation_score'])
plt.ylabel('Meditation Score')
plt.xlabel('Time')
plt.title('Meditation Quality Over Time')
plt.tight_layout()
plt.savefig('meditation_score.png')
plt.show()
```
"""


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

class DataValidator:
    """Validate data integrity and quality."""

    @staticmethod
    def validate_eeg_data(df, channels=None):
        """Validate EEG data format and values."""
        if channels is None:
            channels = ['Fp1', 'Fp2', 'Fz', 'Pz', 'O1', 'O2']

        issues = []

        # Check columns
        for channel in channels:
            if channel not in df.columns:
                issues.append(f"Missing channel: {channel}")

        # Check timestamp column
        if 'timestamp' not in df.columns:
            issues.append("Missing 'timestamp' column")

        # Check for NaN values
        for channel in channels:
            if channel in df.columns:
                nan_count = df[channel].isna().sum()
                if nan_count > 0:
                    issues.append(f"{channel} has {nan_count} NaN values")

        # Check value ranges (typical EEG: -500 to +500 μV)
        for channel in channels:
            if channel in df.columns:
                if (df[channel].abs() > 1000).any():
                    issues.append(f"{channel} has values > ±1000 μV (likely artifact)")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'sample_count': len(df),
            'channels_found': [c for c in channels if c in df.columns]
        }

    @staticmethod
    def validate_heart_rate_data(df):
        """Validate heart rate data format and values."""
        issues = []

        # Check columns
        required_cols = ['timestamp', 'rr_interval_ms']
        for col in required_cols:
            if col not in df.columns:
                issues.append(f"Missing column: {col}")

        # Check RR interval ranges (40-200 bpm = 300-1500 ms)
        if 'rr_interval_ms' in df.columns:
            invalid_rr = (df['rr_interval_ms'] < 300) | (df['rr_interval_ms'] > 1500)
            if invalid_rr.any():
                issues.append(f"{invalid_rr.sum()} RR intervals outside physiological range")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'beat_count': len(df)
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("EEG PROCESSOR CONFIGURATION & TESTING UTILITY")
    print("="*70)

    # Save default configuration
    print("\n1. Saving default configuration...")
    TestDataGenerator.save_config_to_file()

    # Print current configuration
    print("\n2. Current Configuration:")
    print("-" * 70)
    print(f"QuestDB Host: {Config.QUESTDB['host']}:{Config.QUESTDB['port']}")
    print(f"EEG Sampling Rate: {Config.EEG['sampling_rate']} Hz")
    print(f"EEG Channels: {', '.join(Config.EEG['channels'])}")
    print(f"Segment Duration: {Config.SEGMENTATION['segment_duration']}s")
    print(f"Overlap: {Config.SEGMENTATION['overlap_ratio']*100:.0f}%")
    print(f"Frequency Bands: {list(Config.FREQUENCY_BANDS.keys())}")

    # Show setup instructions
    print("\n3. Database Setup Instructions:")
    print("-" * 70)
    print("Execute the following SQL in QuestDB:")
    print(QUESTDB_SETUP_SQL)

    # Show quickstart examples
    print("\n4. Quickstart Examples:")
    print("-" * 70)
    print(QUICKSTART_EXAMPLES)

    print("\n" + "="*70)
    print("Ready to use! Import from eeg_processor_questdb module")
    print("="*70)
