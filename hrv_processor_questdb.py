import numpy as np
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import time
import logging
import argparse
from scipy import signal
from scipy.signal import welch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HRVProcessor:
    def __init__(self, host='localhost', port=8812, user='admin', password='quest', session_id=None):
        self.conn_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': 'qdb'
        }
        self.session_id = session_id or f"session_{int(time.time())}"
        self.conn = None
        self.history = {'rmssd': [], 'sdnn': []}
        self.table_initialized = False

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            logger.info(f"✓ Connected to QuestDB at {self.conn_params['host']}")
        except Exception as e:
            logger.error(f"✗ Connection failed: {e}")
            raise

    def setup_table(self):
        """Create the hrv_processed table and clear old session data."""
        try:
            cursor = self.conn.cursor()
            
            # Check for session change and drop table if needed
            cursor.execute("SHOW TABLES")
            tables = [t[0] for t in cursor.fetchall()]
            
            if 'hrv_processed' in tables:
                cursor.execute("SELECT session_id FROM hrv_processed LIMIT 1")
                row = cursor.fetchone()
                if row and row[0] != self.session_id:
                    logger.info(f"New session detected: {self.session_id}. Clearing old data.")
                    cursor.execute("DROP TABLE hrv_processed")
                    self.conn.commit()

            query = """
            CREATE TABLE IF NOT EXISTS hrv_processed (
                timestamp TIMESTAMP,
                session_id STRING,
                sdnn DOUBLE,
                rmssd DOUBLE,
                hf_power DOUBLE,
                hf_norm DOUBLE,
                heart_rate_mean DOUBLE,
                trend_rmssd DOUBLE,
                trend_sdnn DOUBLE
            ) timestamp(timestamp) PARTITION BY DAY;
            """
            cursor.execute(query)
            self.conn.commit()
            cursor.close()
            logger.info("✓ 'hrv_processed' table ready")
            self.table_initialized = True
        except Exception as e:
            logger.error(f"✗ Error setting up table: {e}")

    def fetch_data(self, start_time, end_time):
        try:
            query = f"""
            SELECT timestamp, rr_interval_ms, heart_rate_bpm
            FROM heart_rate_table
            WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
            ORDER BY timestamp
            """
            cursor = self.conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data, columns=['timestamp', 'rr_interval_ms', 'heart_rate_bpm'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            logger.error(f"✗ Error fetching data: {e}")
            return pd.DataFrame()

    def calculate_metrics(self, df):
        if len(df) < 5:
            return None

        rr = df['rr_interval_ms'].values
        hr = df['heart_rate_bpm'].values

        # Time Domain
        sdnn = np.std(rr)
        rmssd = np.sqrt(np.mean(np.diff(rr)**2)) if len(rr) > 1 else 0

        # Frequency Domain (HF Power: 0.15 - 0.4 Hz)
        # Resample RR to 4Hz for frequency analysis
        try:
            # Simple resampling: assume 4Hz sampling of the heart rate signal
            fs = 4.0
            # Preprocessing for Welch
            rr_detrended = signal.detrend(rr)
            nperseg = min(len(rr_detrended), 256)
            freqs, psd = welch(rr_detrended, fs=fs, nperseg=nperseg, nfft=max(nperseg, 256))
            
            hf_mask = (freqs >= 0.15) & (freqs <= 0.4)
            lf_mask = (freqs >= 0.04) & (freqs < 0.15)
            
            hf_power = np.sum(psd[hf_mask])
            lf_power = np.sum(psd[lf_mask])
            total_power = hf_power + lf_power
            
            hf_norm = (hf_power / total_power) if total_power > 0 else 0
        except:
            hf_power = 0
            hf_norm = 0

        # Trends (relative to the first value in this script's history)
        if not self.history['rmssd']:
            trend_rmssd = 0.0
            trend_sdnn = 0.0
        else:
            base_rmssd = self.history['rmssd'][0]
            base_sdnn = self.history['sdnn'][0]
            trend_rmssd = (rmssd - base_rmssd) / base_rmssd * 100 if base_rmssd > 0 else 0
            trend_sdnn = (sdnn - base_sdnn) / base_sdnn * 100 if base_sdnn > 0 else 0

        self.history['rmssd'].append(rmssd)
        self.history['sdnn'].append(sdnn)

        return {
            'timestamp': df['timestamp'].iloc[-1],
            'session_id': self.session_id,
            'sdnn': float(sdnn),
            'rmssd': float(rmssd),
            'hf_power': float(hf_power),
            'hf_norm': float(hf_norm),
            'heart_rate_mean': float(np.mean(hr)),
            'trend_rmssd': float(trend_rmssd),
            'trend_sdnn': float(trend_sdnn)
        }

    def process_real_time(self, duration_seconds):
        logger.info(f"Starting HRV processing for session {self.session_id} ({duration_seconds}s)...")
        
        # 1. Wait for data to start
        start_ts = None
        while start_ts is None:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT min(timestamp) FROM heart_rate_table")
                res = cursor.fetchone()
                if res and res[0]:
                    start_ts = res[0]
                    logger.info(f"✓ Data detected at {start_ts}")
                else:
                    time.sleep(1)
                cursor.close()
            except:
                time.sleep(1)

        end_ts = start_ts + timedelta(seconds=duration_seconds)
        last_processed_ts = start_ts
        window_size = timedelta(seconds=30)
        step_size = timedelta(seconds=5)

        while last_processed_ts < end_ts:
            try:
                # Check for latest data
                cursor = self.conn.cursor()
                cursor.execute("SELECT max(timestamp) FROM heart_rate_table")
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
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Loop error: {e}")
                time.sleep(1)

    def save_metrics(self, m):
        try:
            cursor = self.conn.cursor()
            query = """
            INSERT INTO hrv_processed (
                timestamp, session_id, sdnn, rmssd, hf_power, hf_norm, 
                heart_rate_mean, trend_rmssd, trend_sdnn
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                m['timestamp'], m['session_id'], m['sdnn'], m['rmssd'], 
                m['hf_power'], m['hf_norm'], m['heart_rate_mean'], 
                m['trend_rmssd'], m['trend_sdnn']
            ))
            self.conn.commit()
            cursor.close()
            logger.info(f"✓ Saved HRV: RMSSD={m['rmssd']:.2f}, HR={m['heart_rate_mean']:.1f}")
        except Exception as e:
            logger.error(f"✗ Save failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--session-id', type=str, required=True)
    parser.add_argument('--duration', type=int, default=300)
    args = parser.parse_args()

    processor = HRVProcessor(session_id=args.session_id)
    processor.connect()
    processor.setup_table()
    try:
        processor.process_real_time(args.duration)
    finally:
        if processor.conn:
            processor.conn.close()
