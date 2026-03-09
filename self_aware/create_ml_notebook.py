#!/usr/bin/env python3
"""
Script to generate the ML Next Move Prediction Jupyter notebook.

This creates a comprehensive notebook with multiple ML models for predicting
robot actions from sensor data.
"""

import json
import os

def create_notebook():
    """Generate the ML notebook programmatically."""
    
    cells = []
    
    # Helper function to create cells
    def md(text):
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": text.split('\n')
        }
    
    def code(text):
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": text.split('\n')
        }
    
    # Title and Introduction
    cells.append(md("""# 🤖 PiCrawler ML: Next Move Prediction

## Overview
This notebook demonstrates multiple machine learning approaches for predicting robot actions from sensor data.

**Models Covered:**
1. Random Forest Classifier (Baseline)
2. XGBoost (Performance)
3. LSTM (Sequential/Time-series)
4. 1D CNN (Pattern Recognition)
5. Simple Neural Network (DNN)
6. Decision Tree (Interpretable)

**Dataset:** Real sensor logs from autonomous_navigator_with_logging.py"""))
    
    # Setup
    cells.append(md("## 1. Setup & Imports"))
    cells.append(code("""# Core libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Scikit-learn
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.tree import plot_tree

# Deep learning (TensorFlow/Keras)
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    print(f"✓ TensorFlow {tf.__version__}")
except ImportError:
    print("⚠ TensorFlow not installed (pip install tensorflow)")

# XGBoost
try:
    import xgboost as xgb
    print(f"✓ XGBoost {xgb.__version__}")
except ImportError:
    print("⚠ XGBoost not installed (pip install xgboost)")

print("\\n✓ All imports successful!")"""))
    
    # Data Collection Guide
    cells.append(md("""## 2. Data Collection Guide

### How to Collect Training Data

Run the autonomous navigator with logging enabled:

```bash
# Collect data (10 Hz sampling)
python3 self_aware/autonomous_navigator_with_logging.py --log

# Let robot explore for 10-30 minutes
# Press Ctrl+C to stop

# Data saved to: self_aware/logs/session_YYYY-MM-DD_HH-MM-SS.csv
```

### Expected Data Format

Each row contains:
- **Sensors**: distance, pitch, roll, accel, gyro, floor sensors
- **Context**: robot state, speed, stuck counters
- **Action**: The action taken (forward, backward, turn_left, turn_right, etc.)

### Minimum Data Requirements
- **Small dataset**: 1,000+ samples (5-10 min)
- **Good dataset**: 10,000+ samples (30 min)
- **Excellent dataset**: 50,000+ samples (multiple sessions)"""))
    
    # Load Data
    cells.append(md("## 3. Load and Explore Data"))
    cells.append(code("""# Load logged data
log_dir = Path("self_aware/logs")

# Find all session files
log_files = sorted(log_dir.glob("session_*.csv"))
print(f"Found {len(log_files)} log files")

if len(log_files) == 0:
    print("\\n⚠ No log files found!")
    print("Please run: python3 self_aware/autonomous_navigator_with_logging.py --log")
    df = None
else:
    # Load all sessions
    dfs = []
    for log_file in log_files:
        df_temp = pd.read_csv(log_file)
        print(f"  {log_file.name}: {len(df_temp)} samples")
        dfs.append(df_temp)
    
    df = pd.concat(dfs, ignore_index=True)
    print(f"\\n✓ Loaded {len(df)} total samples")
    print(f"  Features: {len(df.columns)}")
    print(f"  Duration: {df['timestamp'].max() - df['timestamp'].min():.1f}s")"""))
    
    cells.append(code("""# Display first few rows
if df is not None:
    display(df.head())"""))
    
    cells.append(code("""# Data statistics
if df is not None:
    print("Dataset Shape:", df.shape)
    print("\\nAction Distribution:")
    print(df['action'].value_counts())
    print("\\nState Distribution:")
    print(df['state'].value_counts())"""))
    
    # Visualization
    cells.append(md("## 4. Data Visualization"))
    cells.append(code("""if df is not None:
    # Action distribution
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 3, 1)
    df['action'].value_counts().plot(kind='bar')
    plt.title('Action Distribution')
    plt.xlabel('Action')
    plt.ylabel('Count')
    
    plt.subplot(1, 3, 2)
    df['state'].value_counts().plot(kind='bar')
    plt.title('State Distribution')
    plt.xlabel('State')
    plt.ylabel('Count')
    
    plt.subplot(1, 3, 3)
    plt.hist(df['distance_cm'], bins=50, edgecolor='black')
    plt.title('Distance Sensor Distribution')
    plt.xlabel('Distance (cm)')
    plt.ylabel('Frequency')
    
    plt.tight_layout()
    plt.show()"""))
    
    # Preprocessing
    cells.append(md("## 5. Data Preprocessing"))
    cells.append(code("""if df is not None:
    # Select features for ML
    feature_columns = [
        'distance_cm', 'pitch', 'roll',
        'accel_x', 'accel_y', 'accel_z',
        'gyro_x', 'gyro_y', 'gyro_z',
        'floor_fl', 'floor_fr', 'floor_bl', 'floor_br',
        'current_speed', 'tilt_magnitude', 'floor_danger_count',
        'consecutive_obstacles', 'consecutive_floor_dangers'
    ]
    
    X = df[feature_columns].values
    y = df['action'].values
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    print(f"Features shape: {X.shape}")
    print(f"Labels shape: {y_encoded.shape}")
    print(f"\\nAction classes: {label_encoder.classes_}")
    print(f"Number of classes: {len(label_encoder.classes_)}")"""))
    
    cells.append(code("""# Train/test split
if df is not None:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")"""))
    
    # Model 1: Random Forest
    cells.append(md("## 6. Model 1: Random Forest Classifier"))
    cells.append(code("""if df is not None:
    # Train Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        random_state=42,
        n_jobs=-1
    )
    
    print("Training Random Forest...")
    rf_model.fit(X_train, y_train)
    
    # Predictions
    y_pred_rf = rf_model.predict(X_test)
    
    # Evaluate
    accuracy_rf = accuracy_score(y_test, y_pred_rf)
    print(f"\\n✓ Random Forest Accuracy: {accuracy_rf:.4f}")
    print("\\nClassification Report:")
    print(classification_report(y_test, y_pred_rf, target_names=label_encoder.classes_))"""))
    
    cells.append(code("""# Feature importance
if df is not None:
    importance_rf = pd.DataFrame({
        'feature': feature_columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    plt.figure(figsize=(10, 6))
    plt.barh(importance_rf['feature'][:15], importance_rf['importance'][:15])
    plt.xlabel('Importance')
    plt.title('Top 15 Feature Importances (Random Forest)')
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()
    
    print("\\nTop 10 Features:")
    display(importance_rf.head(10))"""))
    
    # Model 2: XGBoost
    cells.append(md("## 7. Model 2: XGBoost"))
    cells.append(code("""if df is not None and 'xgb' in dir():
    # Train XGBoost
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric='mlogloss'
    )
    
    print("Training XGBoost...")
    xgb_model.fit(X_train, y_train)
    
    # Predictions
    y_pred_xgb = xgb_model.predict(X_test)
    
    # Evaluate
    accuracy_xgb = accuracy_score(y_test, y_pred_xgb)
    print(f"\\n✓ XGBoost Accuracy: {accuracy_xgb:.4f}")
    print("\\nClassification Report:")
    print(classification_report(y_test, y_pred_xgb, target_names=label_encoder.classes_))
elif df is not None:
    print("⚠ XGBoost not installed. Skipping...")"""))
    
    # Model 3: LSTM
    cells.append(md("## 8. Model 3: LSTM (Sequential Model)"))
    cells.append(code("""# Create sequences for LSTM
if df is not None and 'tf' in dir():
    sequence_length = 10  # Use last 10 timesteps
    
    def create_sequences(X, y, seq_length):
        X_seq, y_seq = [], []
        for i in range(len(X) - seq_length):
            X_seq.append(X[i:i+seq_length])
            y_seq.append(y[i+seq_length])
        return np.array(X_seq), np.array(y_seq)
    
    X_train_seq, y_train_seq = create_sequences(X_train_scaled, y_train, sequence_length)
    X_test_seq, y_test_seq = create_sequences(X_test_scaled, y_test, sequence_length)
    
    print(f"Sequence shape: {X_train_seq.shape}")
    print(f"  (samples, timesteps, features)")"""))
    
    cells.append(code("""# Build LSTM model
if df is not None and 'tf' in dir():
    n_features = X_train_seq.shape[2]
    n_classes = len(label_encoder.classes_)
    
    lstm_model = keras.Sequential([
        layers.LSTM(64, input_shape=(sequence_length, n_features), return_sequences=True),
        layers.Dropout(0.3),
        layers.LSTM(32),
        layers.Dropout(0.3),
        layers.Dense(32, activation='relu'),
        layers.Dense(n_classes, activation='softmax')
    ])
    
    lstm_model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("LSTM Architecture:")
    lstm_model.summary()"""))
    
    cells.append(code("""# Train LSTM
if df is not None and 'tf' in dir():
    print("Training LSTM...")
    history_lstm = lstm_model.fit(
        X_train_seq, y_train_seq,
        validation_split=0.2,
        epochs=20,
        batch_size=32,
        verbose=1
    )
    
    # Evaluate
    y_pred_lstm = np.argmax(lstm_model.predict(X_test_seq), axis=1)
    accuracy_lstm = accuracy_score(y_test_seq, y_pred_lstm)
    print(f"\\n✓ LSTM Accuracy: {accuracy_lstm:.4f}")"""))
    
    # Model 4: CNN
    cells.append(md("## 9. Model 4: 1D CNN"))
    cells.append(code("""# Build 1D CNN model
if df is not None and 'tf' in dir():
    cnn_model = keras.Sequential([
        layers.Conv1D(64, 3, activation='relu', input_shape=(sequence_length, n_features)),
        layers.MaxPooling1D(2),
        layers.Conv1D(32, 3, activation='relu'),
        layers.GlobalAveragePooling1D(),
        layers.Dense(32, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(n_classes, activation='softmax')
    ])
    
    cnn_model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("1D CNN Architecture:")
    cnn_model.summary()"""))
    
    cells.append(code("""# Train CNN
if df is not None and 'tf' in dir():
    print("Training 1D CNN...")
    history_cnn = cnn_model.fit(
        X_train_seq, y_train_seq,
        validation_split=0.2,
        epochs=20,
        batch_size=32,
        verbose=1
    )
    
    # Evaluate
    y_pred_cnn = np.argmax(cnn_model.predict(X_test_seq), axis=1)
    accuracy_cnn = accuracy_score(y_test_seq, y_pred_cnn)
    print(f"\\n✓ 1D CNN Accuracy: {accuracy_cnn:.4f}")"""))
    
    # Model 5: Simple DNN
    cells.append(md("## 10. Model 5: Simple Neural Network"))
    cells.append(code("""# Build DNN model
if df is not None and 'tf' in dir():
    dnn_model = keras.Sequential([
        layers.Dense(128, activation='relu', input_shape=(n_features,)),
        layers.Dropout(0.3),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(32, activation='relu'),
        layers.Dense(n_classes, activation='softmax')
    ])
    
    dnn_model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    
    print("DNN Architecture:")
    dnn_model.summary()"""))
    
    cells.append(code("""# Train DNN
if df is not None and 'tf' in dir():
    print("Training DNN...")
    history_dnn = dnn_model.fit(
        X_train_scaled, y_train,
        validation_split=0.2,
        epochs=30,
        batch_size=32,
        verbose=1
    )
    
    # Evaluate
    y_pred_dnn = np.argmax(dnn_model.predict(X_test_scaled), axis=1)
    accuracy_dnn = accuracy_score(y_test, y_pred_dnn)
    print(f"\\n✓ DNN Accuracy: {accuracy_dnn:.4f}")"""))
    
    # Model 6: Decision Tree
    cells.append(md("## 11. Model 6: Decision Tree (Interpretable)"))
    cells.append(code("""if df is not None:
    # Train Decision Tree
    dt_model = DecisionTreeClassifier(max_depth=10, random_state=42)
    
    print("Training Decision Tree...")
    dt_model.fit(X_train, y_train)
    
    # Predictions
    y_pred_dt = dt_model.predict(X_test)
    
    # Evaluate
    accuracy_dt = accuracy_score(y_test, y_pred_dt)
    print(f"\\n✓ Decision Tree Accuracy: {accuracy_dt:.4f}")"""))
    
    cells.append(code("""# Visualize tree (first 3 levels only)
if df is not None:
    plt.figure(figsize=(20, 10))
    plot_tree(dt_model, max_depth=3, feature_names=feature_columns,
              class_names=label_encoder.classes_, filled=True, fontsize=10)
    plt.title('Decision Tree Visualization (Top 3 Levels)')
    plt.tight_layout()
    plt.show()"""))
    
    # Model Comparison
    cells.append(md("## 12. Model Comparison"))
    cells.append(code("""# Compare all models
if df is not None:
    results = {
        'Model': ['Random Forest', 'XGBoost', 'LSTM', '1D CNN', 'DNN', 'Decision Tree'],
        'Accuracy': [
            accuracy_rf if 'accuracy_rf' in locals() else None,
            accuracy_xgb if 'accuracy_xgb' in locals() else None,
            accuracy_lstm if 'accuracy_lstm' in locals() else None,
            accuracy_cnn if 'accuracy_cnn' in locals() else None,
            accuracy_dnn if 'accuracy_dnn' in locals() else None,
            accuracy_dt if 'accuracy_dt' in locals() else None,
        ]
    }
    
    results_df = pd.DataFrame(results).dropna()
    results_df = results_df.sort_values('Accuracy', ascending=False)
    
    print("\\n" + "="*50)
    print("MODEL COMPARISON")
    print("="*50)
    display(results_df)
    
    # Plot comparison
    plt.figure(figsize=(10, 6))
    plt.barh(results_df['Model'], results_df['Accuracy'])
    plt.xlabel('Accuracy')
    plt.title('Model Performance Comparison')
    plt.xlim([0, 1])
    for i, v in enumerate(results_df['Accuracy']):
        plt.text(v + 0.01, i, f'{v:.4f}', va='center')
    plt.tight_layout()
    plt.show()"""))
    
    # Integration Guide
    cells.append(md("""## 13. Integration with Robot

### Save Best Model

```python
# Save Random Forest (example)
import joblib
joblib.dump(rf_model, 'self_aware/models/rf_model.pkl')
joblib.dump(scaler, 'self_aware/models/scaler.pkl')
joblib.dump(label_encoder, 'self_aware/models/label_encoder.pkl')
```

### Load and Use in Robot

```python
from self_aware.data_logger import DataLogger
import joblib

# Load model
model = joblib.load('self_aware/models/rf_model.pkl')
scaler = joblib.load('self_aware/models/scaler.pkl')
encoder = joblib.load('self_aware/models/label_encoder.pkl')

# Predict action
def predict_next_action(sensor_data):
    features = [
        sensor_data['distance'],
        sensor_data['pitch'],
        # ... all features
    ]
    features_scaled = scaler.transform([features])
    prediction = model.predict(features_scaled)[0]
    action = encoder.inverse_transform([prediction])[0]
    return action
```"""))
    
    # Conclusion
    cells.append(md("""## 14. Conclusion & Next Steps

### Key Findings
- Multiple ML models can learn robot navigation patterns
- Random Forest and XGBoost provide good baseline performance
- LSTM and CNN can capture temporal patterns
- Decision trees offer interpretability

### Next Steps
1. **Collect more data** in diverse environments
2. **Feature engineering** (e.g., rate of change, moving averages)
3. **Hyperparameter tuning** using GridSearch
4. **Ensemble methods** combining multiple models
5. **Reinforcement Learning** for optimization
6. **Deploy best model** to robot for real-time prediction

### Resources
- `self_aware/data_logger.py` - Data logging utilities
- `self_aware/autonomous_navigator_with_logging.py` - Autonomous navigation with logging
- `self_aware/AUTONOMOUS_NAVIGATION.md` - System documentation"""))
    
    # Create notebook structure
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.8.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    return notebook


if __name__ == '__main__':
    print("Generating ML Next Move Prediction notebook...")
    notebook = create_notebook()
    
    output_file = "self_aware/ml_next_move_prediction.ipynb"
    with open(output_file, 'w') as f:
        json.dump(notebook, f, indent=2)
    
    print(f"✓ Notebook created: {output_file}")
    print(f"  Total cells: {len(notebook['cells'])}")
    print("\nTo use:")
    print(f"  jupyter notebook {output_file}")
