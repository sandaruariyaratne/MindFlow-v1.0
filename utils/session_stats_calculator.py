import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class SessionStatsCalculator:
    def __init__(self, host='localhost', port=8812, user='admin', password='quest'):
        self.conn_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': 'qdb'
        }
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            logger.info("✓ Connected to QuestDB for statistics calculation")
        except Exception as e:
            logger.error(f"✗ Failed to connect to QuestDB: {e}")
            raise

    def setup_stats_table(self):
        """Create the session_features_stats table if it doesn't exist."""
        # We will store one row per feature per session for maximum flexibility
        query = """
        CREATE TABLE IF NOT EXISTS session_features_stats (
            timestamp TIMESTAMP,
            session_id STRING,
            feature_name STRING,
            mean DOUBLE,
            std_dev DOUBLE,
            variance DOUBLE,
            min_val DOUBLE,
            max_val DOUBLE,
            median DOUBLE,
            sample_count INT
        ) timestamp(timestamp) PARTITION BY DAY;
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.conn.commit()
            cursor.close()
            logger.info("✓ 'session_features_stats' table ready")
        except Exception as e:
            logger.error(f"✗ Error setting up stats table: {e}")

    def calculate_and_store_stats(self):
        logger.info("Fetching data from 'final_features'...")
        try:
            query = "SELECT * FROM final_features"
            df = pd.read_sql(query, self.conn)
            
            if df.empty:
                logger.warning("No data found in 'final_features'. Cannot calculate statistics.")
                return

            # Ensure timestamp is datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # List of numeric features to analyze
            features = [
                'Alpha', 'Theta', 'Alpha_Beta_Ratio', 'Theta_Alpha_Ratio',
                'RMSSD', 'HF_Power', 'HF_Norm', 'SDNN', 'Heart_Rate_Mean',
                'Trend_RMSSD', 'Trend_SDNN', 'Beta_Theta_Ratio'
            ]

            # Group by session_id
            sessions = df.groupby('session_id')
            
            self.setup_stats_table()
            cursor = self.conn.cursor()
            
            insert_query = """
            INSERT INTO session_features_stats (
                timestamp, session_id, feature_name, mean, std_dev, variance, 
                min_val, max_val, median, sample_count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            processed_at = datetime.now()
            
            for session_id, session_df in sessions:
                logger.info(f"Processing session: {session_id}")
                
                # Check if we already have stats for this session to avoid duplicates
                # In QuestDB we usually append, but for a summary it's good to be clean
                # However, QuestDB doesn't support DELETE well, so we just append with new timestamp
                
                for feature in features:
                    if feature not in session_df.columns:
                        continue
                        
                    data = session_df[feature].dropna()
                    if data.empty:
                        continue
                        
                    stats = {
                        'mean': float(data.mean()),
                        'std': float(data.std()) if len(data) > 1 else 0.0,
                        'var': float(data.var()) if len(data) > 1 else 0.0,
                        'min': float(data.min()),
                        'max': float(data.max()),
                        'median': float(data.median()),
                        'count': int(len(data))
                    }
                    
                    cursor.execute(insert_query, (
                        processed_at,
                        session_id,
                        feature,
                        stats['mean'],
                        stats['std'],
                        stats['var'],
                        stats['min'],
                        stats['max'],
                        stats['median'],
                        stats['count']
                    ))
            
            self.conn.commit()
            cursor.close()
            logger.info(f"✓ Statistics for {len(sessions)} sessions successfully stored in 'session_features_stats'")

        except Exception as e:
            logger.error(f"✗ Error calculating statistics: {e}")

    def close(self):
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    calculator = SessionStatsCalculator()
    try:
        calculator.calculate_and_store_stats()
    finally:
        calculator.close()
