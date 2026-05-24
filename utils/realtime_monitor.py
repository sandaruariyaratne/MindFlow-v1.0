"""
Real-Time EEG Continuous Monitoring Script

This script provides continuous monitoring of meditation metrics with:
- Real-time processing every N seconds
- Live metrics dashboard
- Alert system for state changes
- Session logging and statistics
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from collections import deque
import numpy as np
from eeg_processor_questdb import MeditationProcessor
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('meditation_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RealtimeMetricsMonitor:
    """Continuous real-time meditation metrics monitoring."""

    def __init__(self, check_interval=60, data_window=5, history_size=100):
        """
        Initialize monitor.

        Args:
            check_interval (int): Processing interval in seconds
            data_window (int): Data window in minutes
            history_size (int): Number of samples to keep in history
        """
        self.check_interval = check_interval
        self.data_window = data_window
        self.history_size = history_size

        # Initialize processor
        self.processor = MeditationProcessor()

        # Metrics history (deque for efficient circular buffer)
        self.metrics_history = deque(maxlen=history_size)
        self.session_start = datetime.now()
        self.session_id = f"session_{self.session_start.strftime('%Y%m%d_%H%M%S')}"

        # Thresholds for alerts
        self.thresholds = {
            'excellent_meditation': 0.75,
            'good_meditation': 0.55,
            'fair_meditation': 0.35,
            'stress_alert': 0.25
        }

        # State tracking
        self.current_state = 'idle'
        self.state_duration = 0
        self.monitoring_active = False

    def classify_meditation_state(self, score):
        """
        Classify meditation state based on score.

        Args:
            score (float): Meditation score (0-1)

        Returns:
            tuple: (state_name, quality_description)
        """
        if score >= self.thresholds['excellent_meditation']:
            return ('excellent', 'Deep meditation state')
        elif score >= self.thresholds['good_meditation']:
            return ('good', 'Relaxed meditation state')
        elif score >= self.thresholds['fair_meditation']:
            return ('fair', 'Moderate meditation state')
        elif score >= self.thresholds['stress_alert']:
            return ('alert', 'Alert/Active state')
        else:
            return ('stress', 'Stressed/Anxious state')

    def fetch_and_process(self):
        """Fetch and process latest data."""
        try:
            # Fetch data
            eeg_data = self.processor.db.fetch_last_n_minutes(minutes=self.data_window)
            hr_data = self.processor.db.fetch_heart_rate_data(minutes=self.data_window)

            if eeg_data.empty:
                logger.warning("No EEG data available")
                return None

            # Process
            processed_features = self.processor.preprocessor.process_eeg_data(eeg_data, hr_data)

            if not processed_features:
                return None

            # Calculate statistics
            stats = self._calculate_statistics(processed_features)
            stats['timestamp'] = datetime.now()
            stats['session_id'] = self.session_id

            return stats

        except Exception as e:
            logger.error(f"Error in fetch_and_process: {e}")
            return None

    def _calculate_statistics(self, processed_features):
        """Calculate statistics from processed features."""
        stats = {}

        # Keys to aggregate
        aggregate_keys = [
            'alpha_power', 'beta_power', 'theta_power', 'gamma_power',
            'alpha_beta_ratio', 'theta_alpha_ratio', 'beta_theta_ratio',
            'theta_beta_ratio', 'meditation_score'
        ]

        for key in aggregate_keys:
            values = [f.get(key, 0) for f in processed_features if isinstance(f.get(key), (int, float))]
            if values:
                stats[f'{key}_mean'] = np.mean(values)
                stats[f'{key}_std'] = np.std(values)
                stats[f'{key}_min'] = np.min(values)
                stats[f'{key}_max'] = np.max(values)

        stats['segment_count'] = len(processed_features)

        return stats

    def update_metrics_history(self, stats):
        """Update metrics history."""
        self.metrics_history.append(stats)

    def check_state_change(self, new_score):
        """Detect and report state changes."""
        new_state, description = self.classify_meditation_state(new_score)

        if new_state != self.current_state:
            logger.warning(
                f"STATE CHANGE: {self.current_state.upper()} → {new_state.upper()} "
                f"({description})"
            )
            self.current_state = new_state
            self.state_duration = 0

            # Generate alert if entering stressed state
            if new_state == 'stress':
                self._generate_alert('stress', description)
            elif new_state == 'excellent':
                self._generate_alert('excellent', 'Excellent meditation achieved!')

        self.state_duration += self.check_interval

    def _generate_alert(self, alert_type, message):
        """Generate alert notification."""
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': self.state_duration
        }

        logger.info(f"[ALERT] {alert_type.upper()}: {message}")

        # Here you could integrate with notification systems
        # - Send email
        # - Push notification
        # - Sound alert
        # - Visual feedback to user
        self._save_alert(alert)

    def _save_alert(self, alert):
        """Save alert to file."""
        try:
            with open(f'alerts_{self.session_id}.log', 'a') as f:
                f.write(json.dumps(alert) + '\n')
        except Exception as e:
            logger.error(f"Error saving alert: {e}")

    def display_dashboard(self, stats):
        """Display live metrics dashboard."""
        if not stats:
            return

        print("\n" + "="*70)
        print(f"MEDITATION MONITOR DASHBOARD - {datetime.now().strftime('%H:%M:%S')}")
        print("="*70)

        # Current session info
        elapsed = datetime.now() - self.session_start
        print(f"\nSession: {self.session_id}")
        print(f"Duration: {elapsed.total_seconds()/60:.1f} minutes")
        print(f"Current State: {self.current_state.upper()}")
        print(f"State Duration: {self.state_duration}s")

        # Meditation score
        med_score = stats.get('meditation_score_mean', 0)
        state, quality = self.classify_meditation_state(med_score)
        score_bar = "█" * int(med_score * 20) + "░" * (20 - int(med_score * 20))
        print(f"\nMeditation Score: [{score_bar}] {med_score:.1%}")
        print(f"Quality: {quality}")

        # Brain wave powers
        print(f"\n--- Brain Wave Powers ---")
        print(f"Theta: {stats.get('theta_power_mean', 0):.2f} ± {stats.get('theta_power_std', 0):.2f}")
        print(f"Alpha: {stats.get('alpha_power_mean', 0):.2f} ± {stats.get('alpha_power_std', 0):.2f}")
        print(f"Beta:  {stats.get('beta_power_mean', 0):.2f} ± {stats.get('beta_power_std', 0):.2f}")
        print(f"Gamma: {stats.get('gamma_power_mean', 0):.2f} ± {stats.get('gamma_power_std', 0):.2f}")

        # Frequency ratios
        print(f"\n--- Frequency Ratios ---")
        print(f"Alpha/Beta: {stats.get('alpha_beta_ratio_mean', 0):.4f}")
        print(f"Theta/Alpha: {stats.get('theta_alpha_ratio_mean', 0):.4f}")
        print(f"Theta/Beta: {stats.get('theta_beta_ratio_mean', 0):.4f}")
        print(f"Beta/Theta: {stats.get('beta_theta_ratio_mean', 0):.4f}")

        # Trend analysis
        if len(self.metrics_history) > 1:
            print(f"\n--- Trend Analysis (last {len(self.metrics_history)} samples) ---")
            recent_scores = [m.get('meditation_score_mean', 0) for m in self.metrics_history]
            trend = "↑ Improving" if recent_scores[-1] > recent_scores[0] else "↓ Declining"
            print(f"Meditation Trend: {trend}")
            print(f"Average Score: {np.mean(recent_scores):.1%}")
            print(f"Min/Max: {np.min(recent_scores):.1%} / {np.max(recent_scores):.1%}")

        print("\n" + "="*70 + "\n")

    def save_session_summary(self):
        """Save session summary to file."""
        if len(self.metrics_history) == 0:
            return

        session_end = datetime.now()
        duration = session_end - self.session_start

        # Calculate session statistics
        scores = [m.get('meditation_score_mean', 0) for m in self.metrics_history]
        avg_score = np.mean(scores)
        max_score = np.max(scores)
        min_score = np.min(scores)

        summary = {
            'session_id': self.session_id,
            'start_time': self.session_start.isoformat(),
            'end_time': session_end.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'samples_collected': len(self.metrics_history),
            'avg_meditation_score': float(avg_score),
            'max_meditation_score': float(max_score),
            'min_meditation_score': float(min_score),
            'final_state': self.current_state,
            'quality': self.classify_meditation_state(avg_score)[1]
        }

        # Save summary
        try:
            with open(f'session_{self.session_id}_summary.json', 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"✓ Session summary saved: {summary}")
        except Exception as e:
            logger.error(f"Error saving session summary: {e}")

        return summary

    def run_continuous_monitoring(self, duration_minutes=None):
        """
        Run continuous monitoring.

        Args:
            duration_minutes (int): Duration in minutes, None for infinite
        """
        self.monitoring_active = True
        start_time = time.time()
        max_duration = (duration_minutes * 60) if duration_minutes else None

        logger.info(f"Starting continuous monitoring (session: {self.session_id})")
        print(f"Monitoring started. Press Ctrl+C to stop.\n")

        try:
            while self.monitoring_active:
                # Check duration
                if max_duration and (time.time() - start_time) > max_duration:
                    logger.info("Session duration reached")
                    break

                # Process data
                logger.info(f"Processing data (window: {self.data_window}min)...")
                stats = self.fetch_and_process()

                if stats:
                    # Update history
                    self.update_metrics_history(stats)

                    # Check state
                    med_score = stats.get('meditation_score_mean', 0)
                    self.check_state_change(med_score)

                    # Display dashboard
                    self.display_dashboard(stats)

                    # Update database
                    try:
                        self.processor.db.update_processed_data(data_dict={
                            'timestamp': stats['timestamp'],
                            'session_id': self.session_id,
                            'segment_number': len(self.metrics_history),
                            'meditation_score': med_score,
                            'alpha_beta_ratio': stats.get('alpha_beta_ratio_mean', 0),
                            'theta_alpha_ratio': stats.get('theta_alpha_ratio_mean', 0),
                            'beta_theta_ratio': stats.get('beta_theta_ratio_mean', 0),
                            'theta_beta_ratio': stats.get('theta_beta_ratio_mean', 0),
                            'alpha_power': stats.get('alpha_power_mean', 0),
                            'beta_power': stats.get('beta_power_mean', 0),
                            'theta_power': stats.get('theta_power_mean', 0),
                            'gamma_power': stats.get('gamma_power_mean', 0)
                        })
                    except Exception as e:
                        logger.error(f"Error updating database: {e}")

                else:
                    logger.warning("No data processed in this cycle")

                # Wait before next processing
                logger.info(f"Next processing in {self.check_interval}s...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        except Exception as e:
            logger.error(f"Error in monitoring: {e}")
        finally:
            self.monitoring_active = False
            self.processor.db.close()

            # Save session summary
            summary = self.save_session_summary()
            if summary:
                print("\n" + "="*70)
                print("SESSION SUMMARY")
                print("="*70)
                print(f"Duration: {summary['duration_seconds']/60:.1f} minutes")
                print(f"Samples: {summary['samples_collected']}")
                print(f"Avg Score: {summary['avg_meditation_score']:.1%}")
                print(f"Quality: {summary['quality']}")
                print("="*70 + "\n")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Create monitor
    monitor = RealtimeMetricsMonitor(
        check_interval=60,  # Check every 60 seconds
        data_window=5,      # Process 5 minutes of data each time
        history_size=100    # Keep last 100 samples
    )

    # Run continuous monitoring for 30 minutes (or until Ctrl+C)
    monitor.run_continuous_monitoring(duration_minutes=30)
