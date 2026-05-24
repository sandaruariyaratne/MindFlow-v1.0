"""
Quick-Start Guide for Meditation Score Prediction Model
========================================================

This file contains example data, usage patterns, and setup instructions.
"""

# ======================== QUICK START ========================

"""
STEP 1: Install Dependencies
-----------------------------

pip install tensorflow tensorflow-hub numpy pandas scikit-learn matplotlib

For GPU support (optional, speeds up training 10-100x):
pip install tensorflow[and-cuda]  # or tensorflow[and-rocm] for AMD


STEP 2: Prepare Your Data
--------------------------

Your CSV file should have this format (12 input features + 1 target):

    Alpha,Theta,Alpha-Beta Ratio,Theta-Alpha Ratio,RMSSD,HF Power,HF Norm,SDNN,Heart Rate Mean,Trend RMSSD,Trend SDNN,Beta-Theta Ratio,Meditation Score
    52.3,7.8,0.48,0.15,58,1800,0.38,125,72,0.5,2.1,1.0,7.5
    45.1,8.2,0.45,0.18,72,2300,0.42,150,65,1.2,4.5,0.9,8.2
    ...


STEP 3: Train the Model
-----------------------

python train_meditation_model.py --data your_data.csv --epochs 200 --output ./models


STEP 4: Use the Model
---------------------

from train_meditation_model import load_saved_model
import numpy as np

model, scaler = load_saved_model('./models')

# Your 12 metrics
metrics = np.array([[52.3, 7.8, 0.48, 0.15, 58, 1800, 0.38, 125, 72, 0.5, 2.1, 1.0]])

# Scale and predict
scaled = scaler.transform(metrics)
score = model.predict(scaled)[0][0] * 10
print(f"Meditation Score: {score:.2f}/10")
"""

# ======================== EXAMPLE DATA ========================

EXAMPLE_DATA = """Alpha,Theta,Alpha-Beta Ratio,Theta-Alpha Ratio,RMSSD,HF Power,HF Norm,SDNN,Heart Rate Mean,Trend RMSSD,Trend SDNN,Beta-Theta Ratio,Meditation Score
38.2,5.1,0.35,0.13,25,800,0.25,50,85,1.5,3.2,1.5,1.2
42.5,6.3,0.38,0.15,35,1100,0.30,65,80,1.0,2.8,1.3,2.5
48.7,7.2,0.42,0.16,48,1500,0.35,95,75,0.5,2.2,1.1,4.3
55.3,8.5,0.50,0.17,68,2100,0.42,130,68,0.2,1.5,0.9,6.7
62.1,9.2,0.58,0.18,82,2800,0.48,160,62,-0.5,0.8,0.8,8.5
65.8,9.8,0.62,0.19,95,3200,0.52,175,58,-1.0,0.3,0.7,9.2
50.2,7.8,0.46,0.16,60,1900,0.40,120,70,0.0,1.8,1.0,6.0
44.3,6.5,0.39,0.15,42,1300,0.32,75,78,0.8,2.5,1.2,3.8
58.9,8.1,0.54,0.17,75,2400,0.45,145,64,0.0,1.0,0.85,7.8
40.1,5.8,0.36,0.14,30,900,0.28,55,82,1.2,3.0,1.4,1.8
52.4,7.5,0.48,0.17,65,2000,0.41,125,69,0.1,1.6,0.95,6.5
60.7,8.9,0.56,0.18,85,2700,0.48,160,61,-0.8,0.5,0.8,8.9
47.2,7.1,0.43,0.15,55,1700,0.37,110,72,0.4,2.0,1.05,5.5
54.5,8.2,0.50,0.17,72,2200,0.43,140,66,-0.3,1.2,0.92,7.2
41.8,6.0,0.38,0.14,38,1000,0.30,65,81,1.0,2.8,1.35,2.2
56.2,8.0,0.52,0.17,78,2500,0.46,150,63,-0.2,0.9,0.88,8.1
45.6,6.8,0.41,0.15,48,1400,0.34,90,77,0.7,2.3,1.15,4.0
61.3,9.1,0.59,0.19,88,2900,0.50,165,60,-1.2,0.4,0.75,9.0
53.8,7.9,0.49,0.17,70,2100,0.42,135,68,0.0,1.4,0.98,6.8
43.2,6.2,0.39,0.14,40,1100,0.31,70,79,0.9,2.6,1.32,2.8"""

# ======================== EXAMPLE USAGE ========================

def example_1_load_data():
    """Example 1: Load example data"""
    import pandas as pd
    from io import StringIO
    
    df = pd.read_csv(StringIO(EXAMPLE_DATA))
    print("✅ Loaded example data")
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"Meditation scores range: {df['Meditation Score'].min()}-{df['Meditation Score'].max()}")
    
    return df


def example_2_save_example_csv():
    """Example 2: Save example data to CSV file"""
    with open('meditation_example_data.csv', 'w') as f:
        f.write(EXAMPLE_DATA)
    print("✅ Saved example data to meditation_example_data.csv")


def example_3_train_on_example_data():
    """Example 3: Train model on example data"""
    import pandas as pd
    from io import StringIO
    from train_meditation_model import train_model, save_model
    
    # Load example data
    df = pd.read_csv(StringIO(EXAMPLE_DATA))
    
    # Train model
    model, scaler, history, metrics, test_data = train_model(
        df, 
        epochs=150,
        batch_size=8,
        test_size=0.2
    )
    
    # Save
    save_model(model, scaler, metrics, output_dir='./example_model')
    print("✅ Model trained and saved")
    
    return model, scaler


def example_4_make_predictions():
    """Example 4: Make predictions with trained model"""
    import numpy as np
    from train_meditation_model import load_saved_model
    
    # Load model
    model, scaler = load_saved_model('./example_model')
    
    # Test data samples
    test_samples = [
        # Deep meditation (high scores expected)
        [62.1, 9.2, 0.58, 0.18, 82, 2800, 0.48, 160, 62, -0.5, 0.8, 0.8],
        # Moderate meditation
        [50.2, 7.8, 0.46, 0.16, 60, 1900, 0.40, 120, 70, 0.0, 1.8, 1.0],
        # Distracted/low meditation (low scores expected)
        [38.2, 5.1, 0.35, 0.13, 25, 800, 0.25, 50, 85, 1.5, 3.2, 1.5],
    ]
    
    test_samples = np.array(test_samples)
    scaled = scaler.transform(test_samples)
    predictions = model.predict(scaled, verbose=0) * 10
    
    labels = ["Deep Meditation", "Moderate Meditation", "Distracted"]
    
    print("\n🔮 Predictions:")
    for i, (pred, label) in enumerate(zip(predictions, labels)):
        print(f"  {label}: {pred[0]:.2f}/10")


def example_5_analyze_metrics():
    """Example 5: Analyze metric distributions"""
    import pandas as pd
    from io import StringIO
    
    df = pd.read_csv(StringIO(EXAMPLE_DATA))
    
    print("\n📊 Input Metric Statistics:")
    print(df.describe().round(2))
    
    print("\n🎯 Meditation Score Statistics:")
    print(f"  Mean: {df['Meditation Score'].mean():.2f}")
    print(f"  Std Dev: {df['Meditation Score'].std():.2f}")
    print(f"  Min: {df['Meditation Score'].min():.2f}")
    print(f"  Max: {df['Meditation Score'].max():.2f}")
    
    # Correlation with target
    correlations = df.corr()['Meditation Score'].sort_values(ascending=False)
    print("\n🔗 Correlation with Meditation Score:")
    for metric, corr in correlations.items():
        if metric != 'Meditation Score':
            print(f"  {metric}: {corr:.3f}")


def example_6_batch_prediction():
    """Example 6: Batch predictions from CSV"""
    import pandas as pd
    import numpy as np
    from train_meditation_model import load_saved_model
    
    # Load model
    model, scaler = load_saved_model('./example_model')
    
    # Load data
    df = pd.read_csv('your_data.csv')
    
    # Extract features (drop target if present)
    feature_cols = ['Alpha', 'Theta', 'Alpha-Beta Ratio', 'Theta-Alpha Ratio',
                   'RMSSD', 'HF Power', 'HF Norm', 'SDNN', 'Heart Rate Mean',
                   'Trend RMSSD', 'Trend SDNN', 'Beta-Theta Ratio']
    
    X = df[feature_cols].values
    
    # Normalize and predict
    X_scaled = scaler.transform(X)
    predictions = model.predict(X_scaled, verbose=0) * 10
    
    # Add to dataframe
    df['Predicted_Score'] = predictions
    
    # Calculate error if actual scores available
    if 'Meditation Score' in df.columns:
        df['Error'] = abs(df['Predicted_Score'] - df['Meditation Score'])
        print(f"\nMean Absolute Error: {df['Error'].mean():.4f}")
    
    # Save results
    df.to_csv('predictions_results.csv', index=False)
    print("✅ Predictions saved to predictions_results.csv")
    print(df[['Predicted_Score', 'Meditation Score', 'Error']].head(10))


def example_7_hyperparameter_tuning():
    """Example 7: Test different hyperparameters"""
    import pandas as pd
    from io import StringIO
    from train_meditation_model import train_model, save_model
    import numpy as np
    
    df = pd.read_csv(StringIO(EXAMPLE_DATA))
    
    hyperparams = [
        {'epochs': 100, 'batch_size': 4},
        {'epochs': 100, 'batch_size': 8},
        {'epochs': 150, 'batch_size': 8},
    ]
    
    results = []
    
    for params in hyperparams:
        print(f"\nTraining with params: {params}")
        model, scaler, history, metrics, _ = train_model(
            df,
            epochs=params['epochs'],
            batch_size=params['batch_size']
        )
        
        results.append({
            'params': params,
            'mae': metrics['mae'],
            'r2': metrics['r2']
        })
        
        print(f"  MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
    
    # Find best
    best = min(results, key=lambda x: x['mae'])
    print(f"\n🏆 Best hyperparameters: {best['params']}")


def example_8_model_comparison():
    """Example 8: Test different architectures"""
    print("""
    To compare different model architectures:
    
    1. Modify build_model() in train_meditation_model.py
    2. Run training multiple times with different architectures
    3. Compare metrics on test set
    
    Example architectures to try:
    
    # Simpler model (for faster training)
    Dense(32) -> ReLU -> Dropout(0.2) -> Dense(16) -> ReLU -> Dense(1)
    
    # Larger model (for more complex patterns)
    Dense(128) -> ReLU -> BatchNorm -> Dropout(0.4) ->
    Dense(64) -> ReLU -> BatchNorm -> Dropout(0.3) ->
    Dense(32) -> ReLU -> Dropout(0.2) ->
    Dense(1)
    
    # With attention mechanism
    Dense(64) -> ReLU -> Attention() -> Dense(32) -> ReLU -> Dense(1)
    """)


# ======================== METRIC RANGES ========================

METRIC_RANGES = {
    "Distracted (0-2)": {
        "Alpha": (20, 40),
        "Theta": (3, 5),
        "RMSSD": (15, 35),
        "SDNN": (30, 60),
        "HF Power": (300, 800),
        "Heart Rate Mean": (80, 100),
    },
    "Unfocused (2-4)": {
        "Alpha": (35, 50),
        "Theta": (5, 7),
        "RMSSD": (30, 50),
        "SDNN": (60, 100),
        "HF Power": (800, 1500),
        "Heart Rate Mean": (75, 85),
    },
    "Moderate Meditation (4-6)": {
        "Alpha": (45, 60),
        "Theta": (6.5, 8.5),
        "RMSSD": (50, 75),
        "SDNN": (100, 150),
        "HF Power": (1500, 2300),
        "Heart Rate Mean": (65, 75),
    },
    "Deep Meditation (6-8)": {
        "Alpha": (55, 70),
        "Theta": (7.5, 9.5),
        "RMSSD": (70, 90),
        "SDNN": (140, 170),
        "HF Power": (2200, 3000),
        "Heart Rate Mean": (55, 70),
    },
    "Peak Meditation (8-10)": {
        "Alpha": (65, 90),
        "Theta": (8.5, 10.5),
        "RMSSD": (85, 120),
        "SDNN": (160, 200),
        "HF Power": (2800, 4000),
        "Heart Rate Mean": (50, 65),
    }
}


def print_metric_ranges():
    """Print expected metric ranges by meditation level"""
    print("\n📊 Expected Metric Ranges by Meditation Level:\n")
    for level, metrics in METRIC_RANGES.items():
        print(f"{level}:")
        for metric, range_vals in metrics.items():
            print(f"  {metric}: {range_vals[0]}-{range_vals[1]}")
        print()


# ======================== TROUBLESHOOTING ========================

TROUBLESHOOTING = """
🔧 TROUBLESHOOTING GUIDE

Problem: "ModuleNotFoundError: No module named 'tensorflow'"
Solution: pip install tensorflow

Problem: "Model predicts same value for all inputs"
Solution: 
  1. Check that scaler.mean_ and scaler.scale_ are loaded correctly
  2. Verify training data has good variance
  3. Check that input normalization matches training preprocessing

Problem: "Very low accuracy (< 70%)"
Solution:
  1. Increase amount of training data (need 300+ samples minimum)
  2. Check that meditation score labels are accurate
  3. Verify all 12 metrics are provided
  4. Try training for more epochs (200-300)
  5. Check that metrics are in expected ranges

Problem: "Training is very slow"
Solution:
  1. Reduce batch size to 16 or 32
  2. Use fewer epochs initially for testing
  3. Enable GPU: pip install tensorflow[and-cuda]
  4. Reduce model size (fewer neurons/layers)

Problem: "Out of memory error"
Solution:
  1. Reduce batch size (try 8 or 16)
  2. Reduce model size
  3. Use data generators for large datasets
  4. Close other applications

Problem: "Loss not decreasing during training"
Solution:
  1. Reduce learning rate (try 0.0005 instead of 0.001)
  2. Increase batch size
  3. Check data for outliers or missing values
  4. Verify features are normalized
"""

print(TROUBLESHOOTING)


# ======================== MAIN ========================

if __name__ == '__main__':
    print("=" * 60)
    print("Meditation Score Prediction - Quick Start Examples")
    print("=" * 60)
    
    print("\n📝 Available examples:")
    print("  1. example_1_load_data() - Load and explore example data")
    print("  2. example_2_save_example_csv() - Save example data to CSV")
    print("  3. example_3_train_on_example_data() - Train on example data")
    print("  4. example_4_make_predictions() - Make predictions")
    print("  5. example_5_analyze_metrics() - Analyze metric distributions")
    print("  6. example_6_batch_prediction() - Batch predictions")
    print("  7. example_7_hyperparameter_tuning() - Test hyperparameters")
    print("  8. example_8_model_comparison() - Compare architectures")
    
    print("\n💾 Example data has 20 meditation sessions with scores 1.2-9.2")
    
    print("\n🚀 Quick start:")
    print("  python quickstart_examples.py")
    print("  >>> example_2_save_example_csv()")
    print("  >>> example_3_train_on_example_data()")
    print("  >>> example_4_make_predictions()")
