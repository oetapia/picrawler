# 🤖 Machine Learning for Next Move Prediction

## Overview

This system enables the PiCrawler robot to collect sensor data during autonomous navigation and train machine learning models to predict optimal actions based on sensor inputs.

**Complete Pipeline:**
1. **Data Collection** → Run robot with logging
2. **Model Training** → Train ML models in Jupyter notebook  
3. **Deployment** → Use trained models for real-time prediction
4. **Continuous Improvement** → Collect more data, retrain

## 📁 Files

### Core Components

| File | Description |
|------|-------------|
| `data_logger.py` | Data logging system (CSV/JSON, 10 Hz sampling) |
| `autonomous_navigator_with_logging.py` | Autonomous navigation with integrated logging |
| `ml_next_move_prediction.ipynb` | Jupyter notebook with 6 ML models |
| `create_ml_notebook.py` | Script to regenerate the notebook |
| `README_ML.md` | This documentation |

### Generated Files

| Location | Content |
|----------|---------|
| `logs/` | Sensor data CSV files from robot sessions |
| `models/` | Trained ML models (pickled) |

## 🚀 Quick Start

### Step 1: Collect Training Data

```bash
# Navigate to project directory
cd /path/to/picrawler

# Run autonomous navigator with logging (10 Hz)
python3 self_aware/autonomous_navigator_with_logging.py --log

# Let robot explore for 10-30 minutes
# Press Ctrl+C when done

# Data saved to: self_aware/logs/session_YYYY-MM-DD_HH-MM-SS.csv
```

**Tips for Quality Data:**
- Run in diverse environments (smooth floors, obstacles, edges)
- Multiple sessions = better model generalization
- Aim for 10,000+ samples minimum (30 min)

### Step 2: Train ML Models

```bash
# Launch Jupyter notebook
jupyter notebook self_aware/ml_next_move_prediction.ipynb

# Or use JupyterLab
jupyter lab self_aware/ml_next_move_prediction.ipynb
```

**In the notebook:**
1. Run all cells sequentially
2. Models will automatically load your logged data
3. Compare model performance
4. Save best model for deployment

### Step 3: Deploy Model (Future)

```python
import joblib
from components.sensors.sensor_fusion import SensorHub

# Load trained model
model = joblib.load('self_aware/models/rf_model.pkl')
scaler = joblib.load('self_aware/models/scaler.pkl')
encoder = joblib.load('self_aware/models/label_encoder.pkl')

# Use in navigation
sensors = SensorHub()
features = [
    sensors.get_distance(),
    *sensors.get_tilt(),
    # ... other features
]
features_scaled = scaler.transform([features])
predicted_action = model.predict(features_scaled)[0]
action_name = encoder.inverse_transform([predicted_action])[0]
```

## 📊 Data Format

### CSV Schema

Each logged row contains 25 features:

| Category | Features |
|----------|----------|
| **Distance** | `distance_cm` |
| **Tilt** | `pitch`, `roll` |
| **Accelerometer** | `accel_x`, `accel_y`, `accel_z` |
| **Gyroscope** | `gyro_x`, `gyro_y`, `gyro_z` |
| **Floor Sensors** | `floor_fl`, `floor_fr`, `floor_bl`, `floor_br` |
| **State** | `state`, `previous_state`, `current_speed` |
| **Context** | `consecutive_obstacles`, `consecutive_floor_dangers`, `stuck_counter` |
| **Action** | `action`, `action_steps`, `action_speed` |
| **Derived** | `tilt_magnitude`, `floor_danger_count` |

### Action Labels

Possible actions the robot can take:
- `forward` - Move forward one step
- `backward` - Move backward  
- `turn_left` - Turn left
- `turn_right` - Turn right
- `balance` - Apply balance correction
- `compact_emergency` - Emergency compact pose
- `emergency_stop` - Full stop
- `none` - No action (rare)

## 🤖 Machine Learning Models

The notebook implements 6 different models:

### 1. **Random Forest** (Baseline)
- **Type**: Ensemble decision trees
- **Best for**: Quick baseline, feature importance
- **Pros**: Fast, interpretable, no scaling needed
- **Cons**: Can overfit, larger model size

### 2. **XGBoost** (Performance)
- **Type**: Gradient boosted trees
- **Best for**: Maximum accuracy
- **Pros**: Often best performance, handles imbalance
- **Cons**: Slower training, more parameters

### 3. **LSTM** (Sequential)
- **Type**: Recurrent neural network
- **Best for**: Time-series patterns
- **Pros**: Captures temporal dependencies
- **Cons**: Requires sequences, slower inference

### 4. **1D CNN** (Pattern Recognition)
- **Type**: Convolutional neural network
- **Best for**: Local patterns in sequences
- **Pros**: Faster than LSTM, good pattern detection
- **Cons**: Requires sequences

### 5. **Simple DNN** (Neural Network)
- **Type**: Multi-layer perceptron
- **Best for**: Non-linear relationships
- **Pros**: Flexible, good with large datasets
- **Cons**: Needs more data, black box

### 6. **Decision Tree** (Interpretable)
- **Type**: Single decision tree
- **Best for**: Understanding decision logic
- **Pros**: Visualizable, very interpretable
- **Cons**: Lower accuracy, prone to overfitting

## 📈 Expected Performance

Based on similar robotics ML tasks:

| Model | Expected Accuracy | Inference Speed | Memory |
|-------|------------------|-----------------|--------|
| Random Forest | 85-92% | ~1 ms | ~10 MB |
| XGBoost | 88-94% | ~1 ms | ~5 MB |
| LSTM | 80-90% | ~5 ms | ~20 MB |
| 1D CNN | 82-91% | ~3 ms | ~15 MB |
| DNN | 83-91% | ~2 ms | ~10 MB |
| Decision Tree | 75-85% | <1 ms | ~1 MB |

**Note**: Actual performance depends on:
- Quality and quantity of training data
- Diversity of scenarios encountered
- Hyperparameter tuning

## 🔧 Advanced Usage

### Custom Logging Rate

```bash
# Collect at 20 Hz (more data)
python3 self_aware/autonomous_navigator_with_logging.py --log --log-rate 20

# Collect at 5 Hz (less storage)
python3 self_aware/autonomous_navigator_with_logging.py --log --log-rate 5
```

### Custom Log Directory

```bash
python3 self_aware/autonomous_navigator_with_logging.py --log --log-dir my_custom_logs
```

### Merge Multiple Sessions

```python
from self_aware.data_logger import merge_log_files, list_log_files

# List all logs
logs = list_log_files("self_aware/logs")

# Merge into single file
merged_df = merge_log_files(logs, "training_data.csv")
```

### View Log Summary

```python
from self_aware.data_logger import print_log_summary

print_log_summary("self_aware/logs")
```

## 🎯 Model Selection Guide

### For Real-time Robot Control
**Recommendation**: Random Forest or XGBoost
- Fast inference (<1 ms)
- No GPU required
- Good accuracy

### For Maximum Accuracy
**Recommendation**: XGBoost with tuning
- Best overall performance
- Handles class imbalance
- Feature importance analysis

### For Learning Temporal Patterns
**Recommendation**: LSTM or 1D CNN
- Captures movement sequences
- Good for predicting multi-step ahead
- Requires more data

### For Interpretability
**Recommendation**: Decision Tree
- Visualizable rules
- Easy to debug
- Export to if/else logic

## 💡 Tips for Better Models

### Data Collection
1. **Diverse scenarios**: Obstacles, edges, tilts, smooth areas
2. **Multiple sessions**: Different times/conditions
3. **Balanced actions**: Ensure all actions well-represented
4. **Quality over quantity**: Clean data > more data

### Feature Engineering
```python
# Add in notebook preprocessing section
df['distance_rate'] = df['distance_cm'].diff()  # Rate of change
df['tilt_rate'] = df['tilt_magnitude'].diff()
df['accel_magnitude'] = np.sqrt(df['accel_x']**2 + df['accel_y']**2 + df['accel_z']**2)
```

### Hyperparameter Tuning
```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [10, 20, 30],
}

grid_search = GridSearchCV(rf_model, param_grid, cv=5)
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
```

## 🐛 Troubleshooting

### No log files found
```bash
# Make sure you ran with --log flag
python3 self_aware/autonomous_navigator_with_logging.py --log
```

### Notebook can't find logs
```python
# Check log directory path
from pathlib import Path
log_dir = Path("self_aware/logs")
print(f"Exists: {log_dir.exists()}")
print(f"Files: {list(log_dir.glob('*.csv'))}")
```

### Low model accuracy
1. Collect more training data (aim for 20k+ samples)
2. Check action distribution (imbalanced classes?)
3. Add more features or feature engineering
4. Try different models or tune hyperparameters
5. Check for sensor noise/outliers

### TensorFlow not installed
```bash
pip install tensorflow
```

### XGBoost not installed
```bash
pip install xgboost
```

## 📚 Additional Resources

### Related Documentation
- `AUTONOMOUS_NAVIGATION.md` - System architecture
- `REFACTORING_GUIDE.md` - Code structure
- `components/sensors/` - Sensor implementations

### Learning Resources
- [Scikit-learn Documentation](https://scikit-learn.org/)
- [TensorFlow Tutorials](https://www.tensorflow.org/tutorials)
- [XGBoost Guide](https://xgboost.readthedocs.io/)

### Example Projects
- Behavior cloning for robots
- Imitation learning from demonstrations
- Reinforcement learning for navigation

## 🔮 Future Enhancements

### Phase 1: Deployment
- [ ] Create ML-based autonomous navigator
- [ ] Real-time inference integration
- [ ] Model switching (fallback to rule-based)
- [ ] Performance profiling

### Phase 2: Advanced ML
- [ ] Reinforcement learning (PPO, DQN)
- [ ] Transfer learning across environments
- [ ] Model compression for edge deployment
- [ ] Active learning (collect edge cases)

### Phase 3: Visual Self-Modeling
- [ ] Camera-based state prediction
- [ ] Forward models (predict outcome)
- [ ] Inverse models (infer action)
- [ ] World models for planning

## 🤝 Contributing

To add new features:

1. **New sensors**: Update `data_logger.py` schema
2. **New models**: Add cells to notebook generator
3. **New features**: Modify feature_columns list
4. **Optimizations**: Profile and optimize bottlenecks

## 📝 License

Same as parent project (see root LICENSE file)

## ✨ Credits

Built on the refactored PiCrawler autonomous navigation system using modular, reusable components.

---

**Questions?** See `AUTONOMOUS_NAVIGATION.md` or check component docstrings.

**Ready to train?** 
```bash
jupyter notebook self_aware/ml_next_move_prediction.ipynb
```
