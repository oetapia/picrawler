# 🚀 ML Quick Start Guide

## 3-Step Process

### Step 1: Collect Data (10-30 minutes)

```bash
cd /path/to/picrawler
python3 self_aware/autonomous_navigator_with_logging.py --log
# Press Ctrl+C when done
```

**Output**: `self_aware/logs/session_YYYY-MM-DD_HH-MM-SS.csv`

### Step 2: Train Models (5-15 minutes)

```bash
jupyter notebook self_aware/ml_next_move_prediction.ipynb
# Run all cells (Cell → Run All)
```

**Models trained**: Random Forest, XGBoost, LSTM, CNN, DNN, Decision Tree

### Step 3: Compare & Deploy

**In notebook**: Check the "Model Comparison" section
- Best accuracy: Usually XGBoost or Random Forest
- Fastest: Decision Tree or Random Forest
- Most interpretable: Decision Tree

**Save best model**:
```python
import joblib
joblib.dump(rf_model, 'self_aware/models/rf_model.pkl')
joblib.dump(scaler, 'self_aware/models/scaler.pkl')
joblib.dump(label_encoder, 'self_aware/models/label_encoder.pkl')
```

## File Overview

```
self_aware/
├── data_logger.py                          # Logging system
├── autonomous_navigator_with_logging.py    # Data collection
├── ml_next_move_prediction.ipynb          # ML training
├── README_ML.md                           # Full documentation
└── logs/                                  # Collected data
    └── session_*.csv
```

## Expected Results

- **Dataset size**: 10k-50k samples (30 min session)
- **Training time**: 2-10 minutes (depends on model)
- **Accuracy**: 85-94% (Random Forest/XGBoost)
- **File size**: 5-10 MB per 30-min session

## Troubleshooting

**No data collected?**
- Make sure you used `--log` flag
- Check `self_aware/logs/` directory

**Notebook can't find data?**
- Run notebook from project root
- Check log file paths in notebook

**Low accuracy?**
- Collect more data (aim for 20k+ samples)
- Try multiple environments
- Check action distribution (balanced?)

## Advanced Options

```bash
# Custom sample rate
python3 self_aware/autonomous_navigator_with_logging.py --log --log-rate 20

# Custom directory
python3 self_aware/autonomous_navigator_with_logging.py --log --log-dir my_logs
```

## Next Steps

1. ✅ Collect diverse data (obstacles, edges, tilts)
2. ✅ Train multiple models
3. ✅ Compare performance
4. 🔜 Deploy best model to robot
5. 🔜 Collect more data, retrain (continuous improvement)

For full documentation, see `README_ML.md`
