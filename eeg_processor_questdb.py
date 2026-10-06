import numpy as np
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import time
import logging
import argparse
from scipy.signal import welch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EEGProcessor:
    def __init__(self, host='localhost', port=8812, user='admin', password='quest', session_id=None):
        self.conn_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': 'qdb'
        }
        self.session_id = session_id or f"session_{int(time.time())}"
        self.sampling_rate = 256.0  # Assumed from generator
        self.conn = None
        self.table_initialized = False

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            logger.info(f"✓ Connected to QuestDB at {self.conn_params['host']}")
        except Exception as e:
            logger.error(f"✗ Connection failed: {e}")
            raise

    def setup_table(self):
        """Create the eeg_processed table and clear old session data."""
        try:
            cursor = self.conn.cursor()
            
            # Check for session change and drop table if needed
            cursor.execute("SHOW TABLES")
            tables = [t[0] for t in cursor.fetchall()]
            
            if 'eeg_processed' in tables:
                cursor.execute("SELECT session_id FROM eeg_processed LIMIT 1")
                row = cursor.fetchone()
                if row and row[0] != self.session_id:
                    logger.info(f"New session detected: {self.session_id}. Clearing old data.")
                    cursor.execute("DROP TABLE eeg_processed")
                    self.conn.commit()

            query = """
            CREATE TABLE IF NOT EXISTS eeg_processed (
                timestamp TIMESTAMP,
                session_id STRING,
                alpha_power DOUBLE,
                theta_power DOUBLE,
                beta_power DOUBLE,
                alpha_beta_ratio DOUBLE,
                theta_alpha_ratio DOUBLE,
                beta_theta_ratio DOUBLE,
                meditation_score DOUBLE
            ) timestamp(timestamp) PARTITION BY DAY;
            """
            cursor.execute(query)
            self.conn.commit()
            cursor.close()
            logger.info("✓ 'eeg_processed' table ready")
            self.table_initialized = True
        except Exception as e:
            logger.error(f"✗ Error setting up table: {e}")

    def fetch_data(self, start_time, end_time):
        try:
            query = f"""
            SELECT timestamp, Fp1, Fp2, Fz, Pz, O1, O2
            FROM eeg_table
            WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
            ORDER BY timestamp
            """
            cursor = self.conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data, columns=['timestamp', 'Fp1', 'Fp2', 'Fz', 'Pz', 'O1', 'O2'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            logger.error(f"✗ Error fetching EEG data: {e}")
            return pd.DataFrame()

    def calculate_metrics(self, df):
        if len(df) < 256: # Need at least 1 second of data
            return None

        # Average across channels for simplicity in meditation score
        channels = ['Fp1', 'Fp2', 'Fz', 'Pz', 'O1', 'O2']
        data = df[channels].mean(axis=1).values
        
        # Compute PSD using Welch
        fs = self.sampling_rate
        freqs, psd = welch(data, fs=fs, nperseg=min(len(data), 256))

        # Band Powers
        theta_mask = (freqs >= 4) & (freqs <= 8)
        alpha_mask = (freqs >= 8) & (freqs <= 13)
        beta_mask = (freqs >= 13) & (freqs <= 30)

        theta = np.sum(psd[theta_mask])
        alpha = np.sum(psd[alpha_mask])
        beta = np.sum(psd[beta_mask])

        # Ratios
        alpha_beta = alpha / beta if beta > 0 else 0
        theta_alpha = theta / alpha if alpha > 0 else 0
        beta_theta = beta / theta if theta > 0 else 0
        
        # A simple meditation score (higher alpha/beta ratio usually means more relaxed)
        meditation_score = np.clip(alpha_beta * 20, 0, 100)

        return {
            'timestamp': df['timestamp'].iloc[-1],
            'session_id': self.session_id,
            'alpha_power': float(alpha),
            'theta_power': float(theta),
            'beta_power': float(beta),
            'alpha_beta_ratio': float(alpha_beta),
            'theta_alpha_ratio': float(theta_alpha),
            'beta_theta_ratio': float(beta_theta),
            'meditation_score': float(meditation_score)
        }

    def process_real_time(self, duration_seconds):
        logger.info(f"Starting EEG processing for session {self.session_id} ({duration_seconds}s)...")
        
        start_ts = None
        while start_ts is None:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT min(timestamp) FROM eeg_table")
                res = cursor.fetchone()
                if res and res[0]:
                    start_ts = res[0]
                    logger.info(f"✓ EEG Data detected at {start_ts}")
                else:
                    time.sleep(1)
                cursor.close()
            except Exception as e:
                self.conn.rollback()
                time.sleep(1)

        end_ts = start_ts + timedelta(seconds=duration_seconds)
        last_processed_ts = start_ts
        window_size = timedelta(seconds=5)
        step_size = timedelta(seconds=2)

        while last_processed_ts < end_ts:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT max(timestamp) FROM eeg_table")
                db_max_ts = cursor.fetchone()[0]
                cursor.close()

                if db_max_ts and db_max_ts >= last_processed_ts + step_size:
                    current_end = last_processed_ts + step_size
                    current_start = current_end - window_size
                    
                    df = self.fetch_data(
                        current_start.strftime('%Y-%m-%d %H:%M:%S.%f'),
                        current_end.strftime('%Y-%m-%d %H:%M:%S.%f')
                    )
                    
                    if not df.empty:
                        metrics = self.calculate_metrics(df)
                        if metrics:
                            self.save_metrics(metrics)
                    
                    last_processed_ts = current_end
                else:
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Loop error: {e}")
                self.conn.rollback()
                time.sleep(1)

    def save_metrics(self, m):
        try:
            cursor = self.conn.cursor()
            query = """
            INSERT INTO eeg_processed (
                timestamp, session_id, alpha_power, theta_power, beta_power, 
                alpha_beta_ratio, theta_alpha_ratio, beta_theta_ratio, meditation_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                m['timestamp'], m['session_id'], m['alpha_power'], m['theta_power'], 
                m['beta_power'], m['alpha_beta_ratio'], m['theta_alpha_ratio'], 
                m['beta_theta_ratio'], m['meditation_score']
            ))
            self.conn.commit()
            cursor.close()
            logger.info(f"✓ Saved EEG: ABR={m['alpha_beta_ratio']:.2f}, Score={m['meditation_score']:.1f}")
        except Exception as e:
            logger.error(f"✗ Save failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--session-id', type=str, required=True)
    parser.add_argument('--duration', type=int, default=300)
    args = parser.parse_args()

    processor = EEGProcessor(session_id=args.session_id)
    processor.connect()
    processor.setup_table()
    try:
        processor.process_real_time(args.duration)
    finally:
        if processor.conn:
            processor.conn.close()
