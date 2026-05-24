import psycopg2
from psycopg2 import sql
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MeditationQualityMonitor:
    def __init__(self, host='localhost', port=8812, user='admin', password='quest'):
        """
        Initialize connection to QuestDB
        
        Args:
            host: QuestDB host address
            port: QuestDB port (default 8812 for PostgreSQL wire protocol)
            user: Database user
            password: Database password
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.conn = None
        self.cursor = None
        
    def connect(self, current_session_id=None):
        """Establish connection to QuestDB"""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='qdb'
            )
            self.cursor = self.conn.cursor()
            logger.info("✓ Connected to QuestDB successfully")
            self.setup_calmness_table(current_session_id)
            return True
        except psycopg2.Error as e:
            logger.error(f"✗ Database connection failed: {e}")
            return False

    def setup_calmness_table(self, current_session_id=None):
        """Create the calmness table if it doesn't exist, clearing old session data if detected."""
        try:
            # Step 1: Check for session mismatch
            if current_session_id:
                try:
                    self.cursor.execute("SELECT session_id FROM calmness LIMIT 1")
                    row = self.cursor.fetchone()
                    if row and row[0] != current_session_id:
                        logger.info(f"New session detected: {current_session_id}. Clearing old calmness data from {row[0]}.")
                        self.cursor.execute("DROP TABLE IF EXISTS calmness")
                        self.conn.commit()
                except Exception:
                    # Table probably doesn't exist yet
                    pass

            # Step 2: Create table fresh
            query = """
            CREATE TABLE IF NOT EXISTS calmness (
                timestamp TIMESTAMP,
                session_id STRING,
                calmness_score DOUBLE,
                Alpha_Beta_Ratio DOUBLE,
                RMSSD DOUBLE
            ) timestamp(timestamp) PARTITION BY DAY;
            """
            self.cursor.execute(query)
            self.conn.commit()
            logger.info("✓ 'calmness' table ready")
        except Exception as e:
            logger.error(f"Error setting up calmness table: {e}")
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Disconnected from QuestDB")
    
    def fetch_latest_metrics(self, session_id=None):
        """
        Fetch latest meditation metrics from final_features table
        """
        try:
            if session_id:
                query = sql.SQL(
                    "SELECT Alpha_Beta_Ratio, RMSSD, timestamp FROM final_features "
                    "WHERE session_id = %s ORDER BY timestamp DESC LIMIT 1"
                )
                self.cursor.execute(query, (session_id,))
            else:
                query = sql.SQL(
                    "SELECT Alpha_Beta_Ratio, RMSSD, timestamp FROM final_features "
                    "ORDER BY timestamp DESC LIMIT 1"
                )
                self.cursor.execute(query)
            
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'Alpha_Beta_Ratio': result[0],
                    'RMSSD': result[1],
                    'timestamp': result[2]
                }
            return None
            
        except psycopg2.Error as e:
            logger.error(f"Error fetching metrics: {e}")
            return None
    
    def calculate_calmness_score(self, alpha_beta_ratio, rmssd):
        """
        Calculate calmness score based on metrics
        """
        # Normalize Alpha-Beta Ratio (typical range 0.5-5.0, optimal 2.0+)
        abr_normalized = min(alpha_beta_ratio / 3.0 * 100, 100)
        
        # Normalize RMSSD (typical range 10-200ms, higher is better)
        rmssd_normalized = min(rmssd / 150.0 * 100, 100)
        
        # Weighted average (60% Alpha-Beta Ratio, 40% RMSSD)
        calmness_score = (abr_normalized * 0.6) + (rmssd_normalized * 0.4)
        
        return round(calmness_score, 2)
    
    def update_calmness_table(self, session_id, calmness_score, alpha_beta_ratio, rmssd):
        """
        Update or insert calmness record in real-time
        """
        try:
            insert_query = sql.SQL(
                "INSERT INTO calmness (session_id, calmness_score, Alpha_Beta_Ratio, "
                "RMSSD, timestamp) VALUES (%s, %s, %s, %s, %s)"
            )
            
            self.cursor.execute(insert_query, (
                session_id,
                calmness_score,
                alpha_beta_ratio,
                rmssd,
                datetime.now()
            ))
            
            self.conn.commit()
            logger.info(
                f"✓ Updated calmness table | Session: {session_id} | "
                f"Score: {calmness_score} | ABR: {alpha_beta_ratio} | RMSSD: {rmssd}"
            )
            return True
            
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error updating calmness table: {e}")
            return False
    
    def process_meditation_session(self, session_id, interval=5, duration=300):
        """
        Continuously monitor and process meditation session metrics
        """
        logger.info(f"Starting meditation quality monitoring for session: {session_id}")
        logger.info(f"Monitoring interval: {interval}s | Duration: {duration}s")
        
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            try:
                metrics = self.fetch_latest_metrics(session_id)
                
                if metrics:
                    alpha_beta_ratio = metrics['Alpha_Beta_Ratio']
                    rmssd = metrics['RMSSD']
                    calmness_score = self.calculate_calmness_score(alpha_beta_ratio, rmssd)
                    
                    self.update_calmness_table(
                        session_id,
                        calmness_score,
                        alpha_beta_ratio,
                        rmssd
                    )
                else:
                    logger.warning(f"No metrics found for session {session_id}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Unexpected error during monitoring: {e}")
                time.sleep(interval)
        
        logger.info(f"Meditation session monitoring completed for {session_id}")
    
    def get_session_summary(self, session_id):
        """
        Get summary statistics for a completed meditation session
        """
        try:
            query = sql.SQL(
                "SELECT AVG(calmness_score) as avg_calmness, "
                "MAX(calmness_score) as max_calmness, "
                "MIN(calmness_score) as min_calmness, "
                "AVG(Alpha_Beta_Ratio) as avg_abr, "
                "AVG(RMSSD) as avg_rmssd, "
                "COUNT(*) as data_points "
                "FROM calmness WHERE session_id = %s"
            )
            
            self.cursor.execute(query, (session_id,))
            result = self.cursor.fetchone()
            
            if result:
                return {
                    'avg_calmness': round(result[0], 2),
                    'max_calmness': round(result[1], 2),
                    'min_calmness': round(result[2], 2),
                    'avg_alpha_beta_ratio': round(result[3], 3),
                    'avg_rmssd': round(result[4], 2),
                    'data_points': result[5]
                }
            return None
            
        except psycopg2.Error as e:
            logger.error(f"Error fetching session summary: {e}")
            return None


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Meditation Quality Monitor')
    parser.add_argument('--session-id', type=str, required=True, help='Session ID')
    parser.add_argument('--duration', type=int, default=120, help='Duration to monitor in seconds')
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = MeditationQualityMonitor(
        host='localhost',
        port=8812,
        user='admin',
        password='quest'
    )
    
    # Connect to database
    if not monitor.connect(current_session_id=args.session_id):
        logger.error("Failed to establish database connection")
        return
    
    try:
        session_id = args.session_id
        session_duration = args.duration
        
        logger.info(f"Monitoring session: {session_id}")
        
        # Start continuous monitoring (Monitor until session ends or timeout)
        monitor.process_meditation_session(
            session_id=session_id,
            interval=2,      # Poll every 2 seconds
            duration=session_duration + 5  # Monitor for the session duration plus a small buffer
        )
        
        # Get session summary after completion
        summary = monitor.get_session_summary(session_id)
        if summary:
            logger.info("=== MEDITATION SESSION SUMMARY ===")
            logger.info(f"Average Calmness Score: {summary['avg_calmness']}")
            logger.info(f"Max Calmness Score: {summary['max_calmness']}")
            logger.info(f"Min Calmness Score: {summary['min_calmness']}")
            logger.info(f"Average Alpha-Beta Ratio: {summary['avg_abr']}")
            logger.info(f"Average RMSSD: {summary['avg_rmssd']}")
            logger.info(f"Total Data Points: {summary['data_points']}")
    
    finally:
        monitor.disconnect()


if __name__ == "__main__":
    main()
