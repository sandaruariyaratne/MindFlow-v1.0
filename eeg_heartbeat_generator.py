"""
EEG and Heart Rate Data Generator for Meditation Measuring Device

This module generates realistic, synchronized EEG (256Hz) and heart rate data
that can be stored in a time series database. The data mimics physiological
patterns observed during meditation states.

EEG Channels: Fp1, Fp2, Fz, Pz, O1, O2
Heart Rate: RR intervals (milliseconds) at realistic sampling rates
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import time
import psycopg2
import psycopg2.extras
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MeditationMetricsGenerator:
    """
    Generates synchronized EEG and heart rate data for meditation sessions.
    """

    def __init__(self, duration_seconds=300, eeg_sampling_rate=256, meditation_state='normal'):
        """
        Initialize the metrics generator.

        Args:
            duration_seconds (int): Duration of the session in seconds (default: 5 minutes)
            eeg_sampling_rate (int): EEG sampling rate in Hz (fixed at 256)
            meditation_state (str): Type of meditation - 'relaxed', 'focused', or 'normal'
        """
        self.duration_seconds = duration_seconds
        self.eeg_sampling_rate = eeg_sampling_rate
        self.meditation_state = meditation_state

        # EEG channels
        self.eeg_channels = ['Fp1', 'Fp2', 'Fz', 'Pz', 'O1', 'O2']

        # Heart rate parameters (bpm based on state)
        self.base_heart_rate = self._get_base_heart_rate()
        self.hr_variability = self._get_hr_variability()

        # Number of samples
        self.n_eeg_samples = duration_seconds * eeg_sampling_rate
        self.start_time = datetime.now()

    def _get_base_heart_rate(self):
        """Get base heart rate based on meditation state."""
        if self.meditation_state == 'relaxed':
            return 55  # Lower HR during deep relaxation
        elif self.meditation_state == 'focused':
            return 65  # Moderate HR during focused meditation
        elif self.meditation_state == 'stress':
            return 85  # Higher HR during stress
        else:
            return 72  # Normal resting HR

    def _get_hr_variability(self):
        """Get heart rate variability (HRV) based on meditation state."""
        if self.meditation_state == 'relaxed':
            return 0.08  # Higher HRV during relaxation (better parasympathetic tone)
        elif self.meditation_state == 'focused':
            return 0.05  # Lower HRV during focused concentration
        elif self.meditation_state == 'stress':
            return 0.03  # Very low HRV during stress (sympathetic dominance)
        else:
            return 0.06  # Normal HRV

    def generate_eeg_signals(self):
        """
        Generate realistic EEG signals for all channels.

        Returns:
            dict: Dictionary with channel names as keys and EEG values as arrays
        """
        time_axis = np.arange(self.n_eeg_samples) / self.eeg_sampling_rate

        eeg_data = {}

        for channel in self.eeg_channels:
            # Base amplitudes tuned to match realistic human PSD power
            # Power scales with amplitude squared. These yield alpha power ~50, theta ~8.
            alpha_amplitude = 10.0
            theta_amplitude = 4.0
            beta_amplitude = 4.4
            gamma_amplitude = 2.0

            # Frequencies
            alpha_freq = np.random.uniform(8, 12)
            theta_freq = np.random.uniform(4, 7)
            beta_freq = np.random.uniform(13, 25)
            gamma_freq = np.random.uniform(30, 45)

            # Meditation state adjustment per component (Targeting ratios between 0.1 and 3.0)
            if self.meditation_state == 'relaxed':
                alpha_amplitude *= 1.4
                theta_amplitude *= 1.2
                beta_amplitude *= 0.8
                noise_level = 1.5
            elif self.meditation_state == 'focused':
                alpha_amplitude *= 1.1
                theta_amplitude *= 1.1
                beta_amplitude *= 1.1
                noise_level = 2.0
            elif self.meditation_state == 'stress':
                alpha_amplitude *= 0.7
                theta_amplitude *= 0.7
                beta_amplitude *= 1.4
                noise_level = 3.5
            else: # normal
                noise_level = 2.0

            alpha_component = alpha_amplitude * np.sin(2 * np.pi * alpha_freq * time_axis)
            theta_component = theta_amplitude * np.sin(2 * np.pi * theta_freq * time_axis)
            beta_component = beta_amplitude * np.sin(2 * np.pi * beta_freq * time_axis)
            gamma_component = gamma_amplitude * np.sin(2 * np.pi * gamma_freq * time_axis)

            # Combine components with channel-specific variations
            # Frontal channels: more beta/theta
            if channel in ['Fp1', 'Fp2', 'Fz']:
                signal = alpha_component * 0.4 + theta_component * 0.5 + beta_component * 0.6 + gamma_component * 0.1
            # Parietal/Occipital: more alpha
            else:
                signal = alpha_component * 0.6 + theta_component * 0.4 + beta_component * 0.4 + gamma_component * 0.1

            # Add realistic noise
            noise = np.random.normal(0, noise_level, self.n_eeg_samples)
            eeg_data[channel] = signal + noise

        return eeg_data

    def generate_heart_rate_intervals(self):
        """
        Generate realistic RR intervals (beat-to-beat intervals in milliseconds).
        
        Returns:
            list: List of RR intervals in milliseconds
        """
        rr_intervals = []
        current_time = 0

        # Generate heart beats throughout the session
        while current_time < self.duration_seconds:
            # Base RR interval in seconds
            base_rr = 60 / self.base_heart_rate

            # HRV has two main components: LF (0.1 Hz) and HF (0.25 Hz - respiration)
            # Tuning these closely matches physiological HF Power (~1000-2000) and LF Power
            lf_component = base_rr * (self.hr_variability * 0.4) * np.sin(2 * np.pi * 0.1 * current_time)
            hf_component = base_rr * (self.hr_variability * 0.6) * np.sin(2 * np.pi * 0.25 * current_time)
            
            hrv_component = lf_component + hf_component

            # Add minor random variation
            random_variation = base_rr * (np.random.normal(0, 0.01))

            # Calculate RR interval
            rr_interval = (base_rr + hrv_component + random_variation) * 1000  # Convert to milliseconds

            # Ensure physiologically realistic bounds (40-120 bpm = 500-1500 ms)
            rr_interval = np.clip(rr_interval, 500, 1500)

            rr_intervals.append(rr_interval)
            current_time += rr_interval / 1000

        return rr_intervals

    def generate_heart_rate_timestamps(self, rr_intervals):
        """
        Generate timestamps for each heartbeat.

        Args:
            rr_intervals (list): List of RR intervals in milliseconds

        Returns:
            list: List of datetime objects for each beat
        """
        timestamps = []
        current_time = self.start_time

        for rr_interval in rr_intervals:
            timestamps.append(current_time)
            current_time += timedelta(milliseconds=rr_interval)

        return timestamps

    def generate_eeg_timestamps(self):
        """
        Generate timestamps for each EEG sample.

        Returns:
            np.ndarray: Array of datetime objects
        """
        timestamps = []
        current_time = self.start_time

        for i in range(self.n_eeg_samples):
            timestamps.append(current_time)
            current_time += timedelta(milliseconds=1000/self.eeg_sampling_rate)

        return np.array(timestamps)

    def create_eeg_dataframe(self):
        """
        Create a pandas DataFrame with EEG data.

        Returns:
            pd.DataFrame: DataFrame with timestamp and all EEG channels
        """
        eeg_signals = self.generate_eeg_signals()
        timestamps = self.generate_eeg_timestamps()

        df = pd.DataFrame({
            'timestamp': timestamps,
            **eeg_signals
        })

        return df

    def create_heart_rate_dataframe(self):
        """
        Create a pandas DataFrame with heart rate data.

        Returns:
            pd.DataFrame: DataFrame with timestamp, RR intervals, and calculated HR
        """
        rr_intervals = self.generate_heart_rate_intervals()
        timestamps = self.generate_heart_rate_timestamps(rr_intervals)

        # Calculate instantaneous heart rate (60000 / RR_interval in ms)
        # Apply clipping to HR (40-120) and RR intervals (500-1500)
        rr_intervals = [max(500, min(1500, rr)) for rr in rr_intervals]
        heart_rates = [max(40, min(120, 60000 / rr)) for rr in rr_intervals]

        df = pd.DataFrame({
            'timestamp': timestamps,
            'rr_interval_ms': rr_intervals,
            'heart_rate_bpm': heart_rates
        })

        return df

    def generate_all_metrics(self):
        """
        Generate all metrics for the session using the configured meditation state.

        Returns:
            tuple: (eeg_dataframe, heart_rate_dataframe)
        """
        logger.info(f"Generating session with {self.meditation_state.upper()} state...")
        
        eeg_df = self.create_eeg_dataframe()
        hr_df = self.create_heart_rate_dataframe()
        
        return eeg_df, hr_df

    def setup_questdb_tables(self, conn):
        """Create eeg_data and heart_rate_data tables in QuestDB if they don't exist."""
        cursor = conn.cursor()
        
        # Create EEG table
        eeg_table_query = """
        CREATE TABLE IF NOT EXISTS eeg_table (
            timestamp TIMESTAMP,
            Fp1 DOUBLE,
            Fp2 DOUBLE,
            Fz DOUBLE,
            Pz DOUBLE,
            O1 DOUBLE,
            O2 DOUBLE
        ) timestamp(timestamp) PARTITION BY DAY;
        """
        
        # Create Heart Rate table
        hr_table_query = """
        CREATE TABLE IF NOT EXISTS heart_rate_table (
            timestamp TIMESTAMP,
            rr_interval_ms DOUBLE,
            heart_rate_bpm DOUBLE
        ) timestamp(timestamp) PARTITION BY DAY;
        """
        
        try:
            cursor.execute("DROP TABLE IF EXISTS eeg_table;")
            cursor.execute("DROP TABLE IF EXISTS heart_rate_table;")
            cursor.execute(eeg_table_query)
            cursor.execute(hr_table_query)
            conn.commit()
            print("✓ QuestDB tables cleared and recreated.")
        except Exception as e:
            print(f"Error setting up QuestDB tables: {e}")
        finally:
            cursor.close()

    def stream_to_questdb_realtime(self, eeg_df, hr_df, host='localhost', port=8812):
        """
        Stream generated data to QuestDB in real time (1-second chunks).
        """
        print("\n" + "="*60)
        print("STARTING REAL-TIME STREAM TO QUESTDB")
        print("="*60)
        
        try:
            conn = psycopg2.connect(
                host=host, port=port, user='admin', password='quest', database='qdb'
            )
            self.setup_questdb_tables(conn)
            cursor = conn.cursor()
            
            # Sort dataframes just in case
            eeg_df = eeg_df.sort_values('timestamp')
            hr_df = hr_df.sort_values('timestamp')
            
            start_time = eeg_df['timestamp'].iloc[0]
            end_time = eeg_df['timestamp'].iloc[-1]
            
            current_time = start_time
            seconds_processed = 0
            
            eeg_columns = ['timestamp', 'Fp1', 'Fp2', 'Fz', 'Pz', 'O1', 'O2']
            hr_columns = ['timestamp', 'rr_interval_ms', 'heart_rate_bpm']
            
            eeg_insert_query = "INSERT INTO eeg_table VALUES %s"
            hr_insert_query = "INSERT INTO heart_rate_table VALUES %s"
            
            print(f"Streaming {self.duration_seconds} seconds of data...")
            
            while current_time < end_time:
                window_end = current_time + timedelta(seconds=1)
                
                # Get 1 second of data
                eeg_chunk = eeg_df[(eeg_df['timestamp'] >= current_time) & (eeg_df['timestamp'] < window_end)]
                hr_chunk = hr_df[(hr_df['timestamp'] >= current_time) & (hr_df['timestamp'] < window_end)]
                
                # Insert EEG chunk
                if not eeg_chunk.empty:
                    eeg_values = [tuple(x) for x in eeg_chunk[eeg_columns].to_numpy()]
                    psycopg2.extras.execute_values(cursor, eeg_insert_query, eeg_values)
                
                # Insert Heart Rate chunk
                if not hr_chunk.empty:
                    hr_values = [tuple(x) for x in hr_chunk[hr_columns].to_numpy()]
                    psycopg2.extras.execute_values(cursor, hr_insert_query, hr_values)
                
                conn.commit()
                
                seconds_processed += 1
                if seconds_processed % 10 == 0:
                    print(f"Streamed {seconds_processed}/{self.duration_seconds} seconds...")
                
                # Simulate real-time by sleeping for 1 second
                time.sleep(1)
                current_time = window_end
                
            print("\n✓ Real-time streaming complete!")
            
        except Exception as e:
            print(f"✗ Database error during streaming: {e}")
        finally:
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()

    def print_summary(self, eeg_df, hr_df):
        """
        Print summary statistics of the generated data.

        Args:
            eeg_df (pd.DataFrame): EEG data
            hr_df (pd.DataFrame): Heart rate data
        """
        print("\n" + "="*60)
        print("MEDITATION METRICS SUMMARY")
        print("="*60)
        print(f"\nSession Duration: {self.duration_seconds} seconds")
        print(f"Meditation State: {self.meditation_state}")
        print(f"EEG Sampling Rate: {self.eeg_sampling_rate} Hz")
        print(f"EEG Samples: {len(eeg_df)}")
        print(f"Heartbeats: {len(hr_df)}")

        print("\n--- EEG Channels Statistics ---")
        for channel in self.eeg_channels:
            mean_val = eeg_df[channel].mean()
            std_val = eeg_df[channel].std()
            min_val = eeg_df[channel].min()
            max_val = eeg_df[channel].max()
            print(f"{channel}: Mean={mean_val:.2f}μV, Std={std_val:.2f}μV, "
                  f"Range=[{min_val:.2f}, {max_val:.2f}]μV")

        print("\n--- Heart Rate Statistics ---")
        mean_hr = hr_df['heart_rate_bpm'].mean()
        std_hr = hr_df['heart_rate_bpm'].std()
        min_hr = hr_df['heart_rate_bpm'].min()
        max_hr = hr_df['heart_rate_bpm'].max()
        mean_rr = hr_df['rr_interval_ms'].mean()

        print(f"Mean Heart Rate: {mean_hr:.1f} bpm")
        print(f"Heart Rate Std Dev: {std_hr:.1f} bpm")
        print(f"Heart Rate Range: [{min_hr:.1f}, {max_hr:.1f}] bpm")
        print(f"Mean RR Interval: {mean_rr:.1f} ms")

        print("\n" + "="*60 + "\n")


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Meditation Data Generator')
    parser.add_argument('--duration', type=int, default=120, help='Session duration in seconds')
    parser.add_argument('--state', type=str, default='relaxed', choices=['relaxed', 'focused', 'stress', 'normal'], 
                        help='Meditation state')
    
    args = parser.parse_args()

    print(f"Generating meditation metrics for {args.duration}s with state: {args.state}...")
    generator = MeditationMetricsGenerator(
        duration_seconds=args.duration,
        eeg_sampling_rate=256,
        meditation_state=args.state
    )

    # Generate all metrics
    eeg_data, hr_data = generator.generate_all_metrics()

    # Stream data to QuestDB in real time
    generator.stream_to_questdb_realtime(eeg_data, hr_data)
    # Print summary statistics
    generator.print_summary(eeg_data, hr_data)
