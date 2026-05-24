"""
Model Prediction and Scoring Script

This script calculates the final model-based meditation score for a session
using the 'mindfulness_model.keras' and stores it alongside the user-reported
score in a new table 'session_predictions'.
"""

import argparse
import logging
import numpy as np
import pandas as pd
import psycopg2
from pathlib import Path
from datetime import datetime
import json

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logging.warning("TensorFlow not found. Will use heuristic fallback for scoring.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Features matching the trained model (12 biometric + 1 categorical)
FEATURES = [
    'alpha', 'theta', 'alpha_beta_ratio', 'theta_alpha_ratio',
    'rmssd', 'hf_power', 'hf_norm', 'sdnn', 'heart_rate_mean',
    'trend_rmssd', 'trend_sdnn', 'beta_theta_ratio'
]

# Categorical encoding mapping
MEDITATION_TYPES = {
    'mindfulness': 0,
    'loving-kindness': 1,
    'body-scan': 2,
    'spiritual': 3,
    'focused': 4,
    'mantra': 5,
    'unknown': 0
}

class ModelPredictor:
    def __init__(self, host='localhost', port=8812, user='admin', password='quest', model_path='mindfulness_model.keras'):
        self.conn_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': 'qdb'
        }
        self.model_path = model_path
        self.model = None
        self.scaler_mean = None
        self.scaler_scale = None
        self.load_scaler()
        self.load_model()
        self.setup_tables()

    def connect(self):
        return psycopg2.connect(**self.conn_params)

    def load_scaler(self):
        """Loads the standard scaler parameters used during training."""
        scaler_path = Path(self.model_path).parent / 'scaler_params.json'
        try:
            if scaler_path.exists():
                with open(scaler_path, 'r') as f:
                    params = json.load(f)
                    self.scaler_mean = np.array(params['mean'])
                    self.scaler_scale = np.array(params['scale'])
                    logger.info("Successfully loaded scaler parameters")
            else:
                logger.warning(f"Scaler file {scaler_path} not found. Predictions may be saturated.")
        except Exception as e:
            logger.error(f"Failed to load scaler: {e}")

    def load_model(self):
        """Loads the pre-trained Keras model."""
        if not TF_AVAILABLE:
            logger.warning("Using heuristic scoring as TF is unavailable.")
            return

        model_file = Path(self.model_path)
        if model_file.exists():
            try:
                # Custom object to ignore 'quantization_config' if present in older TF versions
                class CustomEmbedding(tf.keras.layers.Embedding):
                    def __init__(self, **kwargs):
                        kwargs.pop('quantization_config', None)
                        super().__init__(**kwargs)
                
                self.model = tf.keras.models.load_model(
                    self.model_path, 
                    custom_objects={'Embedding': CustomEmbedding}
                )
                logger.info(f"Successfully loaded model from {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.model = None
        else:
            logger.warning(f"Model file {self.model_path} not found. Using heuristic scoring.")

    def setup_tables(self):
        """Create the target table for predictions if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS session_predictions (
            timestamp TIMESTAMP,
            session_id STRING,
            model_score DOUBLE,
            user_score DOUBLE,
            overall_score DOUBLE
        ) timestamp(timestamp) PARTITION BY DAY;
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✓ 'session_predictions' table ready")
        except Exception as e:
            logger.error(f"✗ Error setting up target table: {e}")

    def fetch_session_data(self, session_id):
        """Fetches final_features for model input."""
        query = """
            SELECT 
                Alpha, Theta, Alpha_Beta_Ratio, Theta_Alpha_Ratio,
                RMSSD, HF_Power, HF_Norm, SDNN, Heart_Rate_Mean,
                Trend_RMSSD, Trend_SDNN, Beta_Theta_Ratio, meditation_type
            FROM final_features
            WHERE session_id = %s
        """
        try:
            conn = self.connect()
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                df = pd.read_sql_query(query, conn, params=[session_id])
            conn.close()
            
            if df.empty:
                logger.warning(f"No biometric data found for session {session_id}")
                return None
                
            df.columns = [col.lower() for col in df.columns]
            return df
        except Exception as e:
            logger.error(f"Database error while fetching features: {e}")
            return None

    def fetch_user_score(self, session_id):
        """Fetches the self-reported quality score from meditation_summaries."""
        query = "SELECT qualityscore FROM meditation_summaries WHERE sessionid = %s LIMIT 1"
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, [session_id])
            res = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if res and res[0] is not None:
                return float(res[0])
            return 5.0 # Default if not found
        except Exception as e:
            logger.error(f"Database error while fetching user score: {e}")
            return 5.0

    def preprocess_data(self, df):
        """Averages features across the session and formats for the dual-input model."""
        # Ensure we have all physiological features
        X_num = pd.DataFrame()
        for feature in FEATURES:
            if feature in df.columns:
                X_num[feature] = df[feature].fillna(df[feature].median())
            else:
                X_num[feature] = 0.0
                
        # Take the mean of physiological features across the session
        numerical_input = X_num.mean().values.reshape(1, 12)
        
        # Apply standard scaling exactly as done in training
        if self.scaler_mean is not None and self.scaler_scale is not None:
            # Prevent division by zero just in case
            safe_scale = np.where(self.scaler_scale == 0, 1e-7, self.scaler_scale)
            numerical_input = (numerical_input - self.scaler_mean) / safe_scale
            
        # Handle meditation type (categorical)
        med_type = df['meditation_type'].iloc[0] if 'meditation_type' in df.columns else 'unknown'
        encoded_type = MEDITATION_TYPES.get(med_type, 0)
        categorical_input = np.array([[encoded_type]], dtype=np.float32)
        
        # Return dict matching the model's InputLayer names
        return {
            'categorical_input': categorical_input,
            'numerical_input': numerical_input
        }

    def heuristic_score(self, model_inputs):
        """Fallback scoring if model is missing."""
        try:
            num_features = model_inputs['numerical_input'][0]
            ab_ratio = num_features[2]
            rmssd = num_features[4]
            
            ab_score = np.clip((ab_ratio - 0.5) / 2.5 * 10, 0, 10)
            hrv_score = np.clip((rmssd - 20) / 80 * 10, 0, 10)
            
            final_score = (ab_score * 0.6) + (hrv_score * 0.4)
            return float(np.clip(final_score, 0, 10))
        except:
            return 5.0

    def save_predictions(self, session_id, model_score, user_score):
        """Inserts the final calculated scores into the database."""
        overall_score = (float(model_score) * 0.6) + (float(user_score) * 0.4)
        
        query = """
            INSERT INTO session_predictions (timestamp, session_id, model_score, user_score, overall_score)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, (datetime.now(), session_id, float(model_score), float(user_score), overall_score))
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✓ Saved scores for {session_id} -> Model: {model_score:.1f}, User: {user_score:.1f}, Overall: {overall_score:.1f}")
        except Exception as e:
            logger.error(f"✗ Failed to save predictions: {e}")

    def run_pipeline(self, session_id):
        logger.info(f"Running prediction pipeline for session: {session_id}")
        
        # 1. Fetch features
        df = self.fetch_session_data(session_id)
        if df is None:
            return False
            
        # 2. Preprocess to shape (1, 13)
        model_input = self.preprocess_data(df)
        
        # 3. Predict Score
        if self.model is not None:
            try:
                # Assuming model outputs a value between 0-1 or 0-10
                prediction = self.model.predict(model_input, verbose=0)
                raw_score = float(prediction[0][0])
                # If model outputs 0-1 probability, scale to 10. Otherwise clip.
                model_score = np.clip(raw_score * 10 if raw_score <= 1.0 else raw_score, 0, 10)
                logger.info(f"Neural Network Prediction: {model_score:.2f}")
            except Exception as e:
                logger.error(f"Model inference failed: {e}. Falling back to heuristic.")
                model_score = self.heuristic_score(model_input)
        else:
            model_score = self.heuristic_score(model_input)
            
        # 4. Fetch User Score
        user_score = self.fetch_user_score(session_id)
        
        # 5. Save to database
        self.save_predictions(session_id, model_score, user_score)
        
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Model Prediction')
    parser.add_argument('--session-id', type=str, required=True, help='Session ID to score')
    parser.add_argument('--model-path', type=str, default='mindfulness_model.keras', help='Path to keras model')
    
    args = parser.parse_args()
    
    predictor = ModelPredictor(model_path=args.model_path)
    predictor.run_pipeline(args.session_id)
