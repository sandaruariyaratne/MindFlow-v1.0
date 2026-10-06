"""
Deep Learning Model for Meditation Score Prediction
=====================================================

This script trains a neural network to predict meditation scores (0-10) from physiological metrics.
Features 12 input metrics: Alpha, Theta, ratios, heart rate variability, and trends.

Usage:
    python train_meditation_model.py --data your_data.csv --epochs 100 --batch-size 32
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import json
import argparse
from pathlib import Path

# ======================== CONFIG ========================

INPUT_FEATURES = [
    'Alpha', 'Theta', 'Alpha-Beta Ratio', 'Theta-Alpha Ratio',
    'RMSSD', 'HF Power', 'HF Norm', 'SDNN', 'Heart Rate Mean',
    'Trend RMSSD', 'Trend SDNN', 'Beta-Theta Ratio'
]

TARGET = 'Meditation Score'

# ======================== DATA GENERATION (FOR TESTING) ========================

def generate_synthetic_data(n_samples=1000):
    """
    Generate synthetic physiological data with realistic relationships to meditation scores.
    Replace this with your actual data loading function.
    """
    np.random.seed(42)
    
    data = {}
    
    # High meditation scores correlate with:
    # - Higher alpha/theta (relaxed state)
    # - Higher HRV (RMSSD, SDNN - healthy autonomic nervous system)
    # - Stable trends
    
    meditation_scores = np.random.uniform(0, 10, n_samples)
    
    # Generate features with correlation to meditation score
    data['Alpha'] = 50 + (meditation_scores * 2) + np.random.normal(0, 10, n_samples)
    data['Theta'] = 8 + (meditation_scores * 0.5) + np.random.normal(0, 3, n_samples)
    data['Alpha-Beta Ratio'] = 0.3 + (meditation_scores * 0.08) + np.random.normal(0, 0.1, n_samples)
    data['Theta-Alpha Ratio'] = 0.15 + np.random.normal(0, 0.05, n_samples)
    data['RMSSD'] = 40 + (meditation_scores * 8) + np.random.normal(0, 15, n_samples)
    data['HF Power'] = 1200 + (meditation_scores * 150) + np.random.normal(0, 500, n_samples)
    data['HF Norm'] = 0.3 + (meditation_scores * 0.04) + np.random.normal(0, 0.1, n_samples)
    data['SDNN'] = 100 + (meditation_scores * 12) + np.random.normal(0, 30, n_samples)
    data['Heart Rate Mean'] = 75 - (meditation_scores * 1) + np.random.normal(0, 5, n_samples)
    data['Trend RMSSD'] = np.random.normal(0, 2, n_samples)
    data['Trend SDNN'] = np.random.normal(0, 3, n_samples)
    data['Beta-Theta Ratio'] = 1.2 - (meditation_scores * 0.05) + np.random.normal(0, 0.3, n_samples)
    data['Meditation Score'] = meditation_scores
    
    df = pd.DataFrame(data)
    
    # Clip to realistic ranges
    df['Alpha'] = df['Alpha'].clip(10, 150)
    df['RMSSD'] = df['RMSSD'].clip(10, 200)
    df['HF Power'] = df['HF Power'].clip(0, 5000)
    df['SDNN'] = df['SDNN'].clip(10, 300)
    df['Heart Rate Mean'] = df['Heart Rate Mean'].clip(40, 120)
    df['Meditation Score'] = df['Meditation Score'].clip(0, 10)
    
    return df

# ======================== MODEL ARCHITECTURE ========================

def build_model(input_dim=12):
    """
    Build a deep neural network with multiple regularization techniques.
    
    Architecture:
    - Input: 12 features
    - Hidden Layer 1: 64 units, ReLU + BatchNorm + Dropout(0.3)
    - Hidden Layer 2: 32 units, ReLU + BatchNorm + Dropout(0.2)
    - Hidden Layer 3: 16 units, ReLU + Dropout(0.1)
    - Output: 1 unit, Sigmoid (0-1 range, scaled to 0-10)
    
    Total trainable parameters: ~3,600
    """
    model = keras.Sequential([
        keras.layers.Dense(64, activation='relu', input_dim=input_dim,
                          kernel_regularizer=keras.regularizers.l2(0.001)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.3),
        
        keras.layers.Dense(32, activation='relu',
                          kernel_regularizer=keras.regularizers.l2(0.001)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        
        keras.layers.Dense(16, activation='relu',
                          kernel_regularizer=keras.regularizers.l2(0.001)),
        keras.layers.Dropout(0.1),
        
        keras.layers.Dense(1, activation='sigmoid')
    ])
    
    return model

# ======================== TRAINING PIPELINE ========================

def train_model(df, epochs=150, batch_size=32, validation_split=0.2, test_size=0.1):
    """
    Train the meditation score prediction model.
    
    Args:
        df: DataFrame with features and target
        epochs: Number of training epochs
        batch_size: Batch size for training
        validation_split: Fraction of training data for validation
        test_size: Fraction of data for testing
    
    Returns:
        model, scaler, history, test_metrics
    """
    
    print("=" * 60)
    print("MEDITATION SCORE PREDICTION MODEL - TRAINING")
    print("=" * 60)
    
    # Extract features and target
    X = df[INPUT_FEATURES].values
    y = df[TARGET].values / 10.0  # Normalize to 0-1 for sigmoid output
    
    print(f"\n📊 Dataset Statistics:")
    print(f"   Total samples: {len(X)}")
    print(f"   Features: {len(INPUT_FEATURES)}")
    print(f"   Score range: {df[TARGET].min():.2f} - {df[TARGET].max():.2f}")
    
    # Split data: train+val / test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    
    # Further split train+val into train / val
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=validation_split, random_state=42
    )
    
    print(f"   Training set: {len(X_train)} samples")
    print(f"   Validation set: {len(X_val)} samples")
    print(f"   Test set: {len(X_test)} samples")
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"\n✅ Standardization complete")
    print(f"   Mean: {scaler.mean_.round(3)}")
    print(f"   Std:  {scaler.scale_.round(3)}")
    
    # Build model
    model = build_model(input_dim=len(INPUT_FEATURES))
    
    print(f"\n🧠 Model Architecture:")
    model.summary()
    
    # Compile
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='mse',
        metrics=['mae']
    )
    
    # Callbacks
    early_stop = keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=20,
        restore_best_weights=True,
        verbose=1
    )
    
    reduce_lr = keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=10,
        min_lr=0.00001,
        verbose=1
    )
    
    # Train
    print(f"\n🚀 Training for {epochs} epochs...")
    history = model.fit(
        X_train_scaled, y_train,
        validation_data=(X_val_scaled, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )
    
    # Evaluate on test set
    print(f"\n📈 Evaluating on test set...")
    y_pred = model.predict(X_test_scaled, verbose=0) * 10  # Scale back to 0-10
    y_test_unscaled = y_test * 10
    
    mse = mean_squared_error(y_test_unscaled, y_pred)
    mae = mean_absolute_error(y_test_unscaled, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test_unscaled, y_pred)
    
    test_metrics = {
        'mse': float(mse),
        'mae': float(mae),
        'rmse': float(rmse),
        'r2': float(r2)
    }
    
    print(f"\n✨ TEST SET METRICS:")
    print(f"   MAE (Mean Absolute Error): {mae:.4f}")
    print(f"   RMSE (Root Mean Squared Error): {rmse:.4f}")
    print(f"   R² Score: {r2:.4f}")
    print(f"   Accuracy: {(1 - mae/10) * 100:.2f}%")
    
    return model, scaler, history, test_metrics, (X_test_scaled, y_test_unscaled, y_pred)

# ======================== VISUALIZATION ========================

def plot_results(history, test_data, output_dir='./'):
    """Generate training and evaluation plots."""
    
    X_test, y_test, y_pred = test_data
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Meditation Score Prediction Model - Results', fontsize=16, fontweight='bold')
    
    # Training history
    axes[0, 0].plot(history.history['loss'], label='Training Loss', linewidth=2)
    axes[0, 0].plot(history.history['val_loss'], label='Validation Loss', linewidth=2)
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss (MSE)')
    axes[0, 0].set_title('Model Loss Over Time')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # MAE
    axes[0, 1].plot(history.history['mae'], label='Training MAE', linewidth=2)
    axes[0, 1].plot(history.history['val_mae'], label='Validation MAE', linewidth=2)
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('MAE')
    axes[0, 1].set_title('Mean Absolute Error')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Predictions vs Actual
    axes[1, 0].scatter(y_test, y_pred, alpha=0.5, s=20)
    min_val = min(y_test.min(), y_pred.min())
    max_val = max(y_test.max(), y_pred.max())
    axes[1, 0].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    axes[1, 0].set_xlabel('Actual Meditation Score')
    axes[1, 0].set_ylabel('Predicted Meditation Score')
    axes[1, 0].set_title('Predictions vs Actual Values')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Residuals
    residuals = y_test - y_pred
    axes[1, 1].scatter(y_pred, residuals, alpha=0.5, s=20)
    axes[1, 1].axhline(y=0, color='r', linestyle='--', linewidth=2)
    axes[1, 1].set_xlabel('Predicted Score')
    axes[1, 1].set_ylabel('Residual (Actual - Predicted)')
    axes[1, 1].set_title('Residual Plot')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = output_dir / 'meditation_model_results.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n📊 Visualization saved to: {output_path}")
    plt.close()

# ======================== SAVE/LOAD UTILITIES ========================

def save_model(model, scaler, metrics, output_dir='./'):
    """Save model, scaler, and metrics."""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Save model
    model_path = output_dir / 'meditation_model.keras'
    model.save(model_path)
    print(f"✅ Model saved to: {model_path}")
    
    # Save scaler parameters
    scaler_params = {
        'mean': scaler.mean_.tolist(),
        'scale': scaler.scale_.tolist(),
        'var': scaler.var_.tolist()
    }
    scaler_path = output_dir / 'scaler_params.json'
    with open(scaler_path, 'w') as f:
        json.dump(scaler_params, f, indent=2)
    print(f"✅ Scaler saved to: {scaler_path}")
    
    # Save metrics
    metrics_path = output_dir / 'metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✅ Metrics saved to: {metrics_path}")

def load_saved_model(model_dir='./'):
    """Load saved model and scaler."""
    
    model_dir = Path(model_dir)
    model = keras.models.load_model(model_dir / 'meditation_model.keras')
    
    with open(model_dir / 'scaler_params.json', 'r') as f:
        scaler_params = json.load(f)
    
    scaler = StandardScaler()
    scaler.mean_ = np.array(scaler_params['mean'])
    scaler.scale_ = np.array(scaler_params['scale'])
    scaler.var_ = np.array(scaler_params['var'])
    
    return model, scaler

# ======================== MAIN ========================

def main():
    parser = argparse.ArgumentParser(description='Train meditation score prediction model')
    parser.add_argument('--data', type=str, default=None, help='Path to CSV file with data')
    parser.add_argument('--epochs', type=int, default=150, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--output', type=str, default='./', help='Output directory for model')
    
    args = parser.parse_args()
    
    # Load or generate data
    if args.data and Path(args.data).exists():
        print(f"📂 Loading data from {args.data}")
        df = pd.read_csv(args.data)
    else:
        print("⚠️  No data file provided. Generating synthetic data for demonstration...")
        df = generate_synthetic_data(n_samples=1000)
        print(f"Generated {len(df)} synthetic samples")
    
    # Train model
    model, scaler, history, metrics, test_data = train_model(
        df, 
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    # Visualize
    plot_results(history, test_data, output_dir=args.output)
    
    # Save
    save_model(model, scaler, metrics, output_dir=args.output)
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE")
    print("=" * 60)
    print(f"\n📁 All outputs saved to: {args.output}")
    print("\nTo use the model in production:")
    print("  1. Load: model, scaler = load_saved_model(model_dir)")
    print("  2. Preprocess: X_scaled = scaler.transform(X)")
    print("  3. Predict: scores = model.predict(X_scaled) * 10")

if __name__ == '__main__':
    main()
