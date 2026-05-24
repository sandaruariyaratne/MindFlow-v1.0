"""
Final Features Aggregator for Meditation BCI

This script combines processed EEG and HRV features into a single 'final_features' 
table in QuestDB. It uses an 'AS OF JOIN' logic to synchronize the two streams,
carrying forward the last known HRV values for every new EEG update.
"""

import psycopg2
from datetime import datetime, timedelta
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinalFeaturesAggregator:
    def __init__(self, host='localhost', port=8812, user='admin', password='quest'):
        self.conn_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': 'qdb'
        }
        self.meditation_type = "unknown"
        self.connect()
        self.setup_table()

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            logger.info("✓ Connected to QuestDB for aggregation")
        except Exception as e:
            logger.error(f"✗ Failed to connect to QuestDB: {e}")
            raise

    def setup_table(self):
        """Create the final_features table with sanitized column names."""
        query = """
        CREATE TABLE IF NOT EXISTS final_features (
            timestamp TIMESTAMP,
            Alpha DOUBLE,
            Theta DOUBLE,
            Alpha_Beta_Ratio DOUBLE,
            Theta_Alpha_Ratio DOUBLE,
            RMSSD DOUBLE,
            HF_Power DOUBLE,
            HF_Norm DOUBLE,
            SDNN DOUBLE,
            Heart_Rate_Mean DOUBLE,
            Trend_RMSSD DOUBLE,
            Trend_SDNN DOUBLE,
            Beta_Theta_Ratio DOUBLE,
            session_id STRING,
            meditation_type STRING
        ) timestamp(timestamp) PARTITION BY DAY;
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()
            cursor.close()
            logger.info("✓ 'final_features' table ready")
        except Exception as e:
            logger.error(f"✗ Error setting up table: {e}")

    def get_last_timestamp(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT max(timestamp) FROM final_features")
            res = cursor.fetchone()
            cursor.close()
            return res[0] if res and res[0] else datetime(2000, 1, 1)
        except:
            return datetime(2000, 1, 1)

    def aggregate_realtime(self, duration_seconds=None, poll_interval=2):
        logger.info(f"Starting real-time feature aggregation (Duration: {duration_seconds if duration_seconds else 'Infinite'}s)...")
        self.current_session_id = None
        start_time = time.time()
        
        while True:
            # Check for duration timeout
            if duration_seconds and (time.time() - start_time) > duration_seconds:
                logger.info(f"Aggregation duration of {duration_seconds}s reached. Stopping.")
                break

            try:
                if self.conn.closed:
                    self.connect()

                # Check for session changes in the source table
                cursor = self.conn.cursor()
                cursor.execute("SELECT session_id FROM eeg_processed LIMIT 1")
                row = cursor.fetchone()
                if row:
                    source_session_id = row[0]
                    
                    # If this is a new session for this aggregator run, check the target table
                    if self.current_session_id != source_session_id:
                        logger.info(f"Source session detected: {source_session_id}")
                        
                        # Check if target table has different data
                        cursor.execute("SELECT session_id FROM final_features LIMIT 1")
                        target_row = cursor.fetchone()
                        
                        if target_row and target_row[0] != source_session_id:
                            logger.info(f"Clearing final_features for new session: {source_session_id}")
                            cursor.execute("DROP TABLE IF EXISTS final_features")
                            self.conn.commit()
                            self.setup_table() # Recreate table
                        
                        self.current_session_id = source_session_id

                last_ts = self.get_last_timestamp()
                
                # QuestDB syntax: table_a ASOF JOIN table_b
                # We filter out rows where critical features are NULL
                query = f"""
                SELECT 
                    e.timestamp, e.alpha_power, e.theta_power, e.alpha_beta_ratio, e.theta_alpha_ratio,
                    h.rmssd, h.hf_power, h.hf_norm, h.sdnn, h.heart_rate_mean,
                    h.trend_rmssd, h.trend_sdnn, e.beta_theta_ratio, e.session_id
                FROM eeg_processed e
                ASOF JOIN hrv_processed h
                WHERE e.timestamp > '{last_ts.strftime('%Y-%m-%d %H:%M:%S.%f')}'
                  AND h.rmssd IS NOT NULL
                  AND h.hf_power IS NOT NULL
                  AND h.sdnn IS NOT NULL
                  AND h.heart_rate_mean IS NOT NULL
                  AND e.alpha_power IS NOT NULL
                  AND e.theta_power IS NOT NULL
                  AND e.alpha_beta_ratio IS NOT NULL
                """

                cursor = self.conn.cursor()
                try:
                    cursor.execute(query)
                    rows = cursor.fetchall()
                except Exception as e:
                    if "table does not exist" in str(e).lower():
                        logger.warning("Source tables (eeg_processed or hrv_processed) not ready yet. Waiting...")
                        rows = []
                    else:
                        raise e
                
                if rows:
                    logger.info(f"Syncing {len(rows)} complete rows (no nulls) to final_features...")
                    insert_query = """
                    INSERT INTO final_features (
                        timestamp, Alpha, Theta, Alpha_Beta_Ratio, Theta_Alpha_Ratio,
                        RMSSD, HF_Power, HF_Norm, SDNN, Heart_Rate_Mean,
                        Trend_RMSSD, Trend_SDNN, Beta_Theta_Ratio, session_id,
                        meditation_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    for row in rows:
                        # Double check for any nulls in the row in Python for extra safety
                        if any(val is None for val in row):
                            continue
                        # Append meditation_type to the row tuple for insertion
                        insert_data = list(row) + [self.meditation_type]
                        cursor.execute(insert_query, insert_data)
                    self.conn.commit()
                
                cursor.close()
                time.sleep(poll_interval)

            except KeyboardInterrupt:
                logger.info("Aggregation stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during aggregation: {e}")
                time.sleep(poll_interval)

    def close(self):
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Final Features Aggregator')
    parser.add_argument('--duration', type=int, default=120, help='Duration to run in seconds')
    # session-id is optional here as the script detects it from eeg_processed
    parser.add_argument('--session-id', type=str, help='Session ID (optional)')
    parser.add_argument('--meditation-type', type=str, default='unknown', help='Type of meditation')
    
    args = parser.parse_args()
    
    aggregator = FinalFeaturesAggregator()
    aggregator.meditation_type = args.meditation_type
    
    try:
        # Buffer the aggregation slightly longer than the generation to ensure all rows sync
        aggregator.aggregate_realtime(duration_seconds=args.duration + 5)
    finally:
        aggregator.close()
