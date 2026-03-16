"""LSTM-based Outbreak Trend Predictor"""
import numpy as np
import logging
from datetime import date, timedelta
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, using statistical fallback for predictions")


class LSTMPredictor(nn.Module):
    """PyTorch LSTM model for time-series case prediction."""

    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=7):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, output_size)
        )

    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out


def predict_trend(case_data: List[int], days_ahead: int = 7) -> List[dict]:
    """
    Predict future case counts using LSTM or statistical fallback.
    
    Args:
        case_data: Historical daily case counts (at least 7 days)
        days_ahead: Number of days to predict
    
    Returns:
        List of prediction dictionaries with date, predicted_cases, confidence bounds
    """
    if len(case_data) < 3:
        return _generate_baseline_predictions(case_data, days_ahead)

    if TORCH_AVAILABLE and len(case_data) >= 14:
        try:
            return _lstm_predict(case_data, days_ahead)
        except Exception as e:
            logger.warning(f"LSTM prediction failed, using fallback: {e}")

    return _statistical_predict(case_data, days_ahead)


def _lstm_predict(case_data: List[int], days_ahead: int) -> List[dict]:
    """Use LSTM model for prediction."""
    # Normalize data
    data = np.array(case_data, dtype=np.float32)
    mean_val = data.mean()
    std_val = data.std() + 1e-8
    normalized = (data - mean_val) / std_val

    # Create sequences
    seq_length = min(14, len(normalized) - 1)
    model = LSTMPredictor(input_size=1, hidden_size=32, num_layers=1, output_size=days_ahead)
    model.eval()

    # Use last seq_length points for prediction
    input_seq = torch.FloatTensor(normalized[-seq_length:]).unsqueeze(0).unsqueeze(-1)

    with torch.no_grad():
        prediction = model(input_seq).squeeze().numpy()

    # Denormalize
    predicted = (prediction * std_val + mean_val).astype(int)
    predicted = np.maximum(predicted, 0)

    # Generate confidence intervals
    today = date.today()
    results = []
    for i in range(days_ahead):
        pred_val = int(predicted[i]) if i < len(predicted) else int(predicted[-1])
        margin = max(int(std_val * (1.5 + i * 0.3)), 50)
        results.append({
            "prediction_date": (today + timedelta(days=i + 1)).isoformat(),
            "predicted_cases": pred_val,
            "confidence_lower": max(0, pred_val - margin),
            "confidence_upper": pred_val + margin,
            "model_type": "lstm"
        })

    return results


def _statistical_predict(case_data: List[int], days_ahead: int) -> List[dict]:
    """Statistical fallback: weighted moving average with trend."""
    data = np.array(case_data[-30:], dtype=np.float64)

    # Calculate trend using linear regression
    x = np.arange(len(data))
    if len(data) > 1:
        slope = np.polyfit(x, data, 1)[0]
    else:
        slope = 0

    # Weighted moving average (recent data weighted more)
    weights = np.exp(np.linspace(-1, 0, min(7, len(data))))
    weights /= weights.sum()
    recent_avg = np.average(data[-len(weights):], weights=weights)

    std_val = np.std(data) if len(data) > 1 else recent_avg * 0.1

    today = date.today()
    results = []
    for i in range(days_ahead):
        pred_val = max(0, int(recent_avg + slope * (i + 1)))
        margin = max(int(std_val * (1.2 + i * 0.2)), 20)
        results.append({
            "prediction_date": (today + timedelta(days=i + 1)).isoformat(),
            "predicted_cases": pred_val,
            "confidence_lower": max(0, pred_val - margin),
            "confidence_upper": pred_val + margin,
            "model_type": "statistical"
        })

    return results


def _generate_baseline_predictions(case_data: List[int], days_ahead: int) -> List[dict]:
    """Generate baseline predictions when insufficient data."""
    base = case_data[-1] if case_data else 100
    today = date.today()
    results = []
    for i in range(days_ahead):
        noise = int(np.random.normal(0, base * 0.1))
        pred = max(0, base + noise)
        results.append({
            "prediction_date": (today + timedelta(days=i + 1)).isoformat(),
            "predicted_cases": pred,
            "confidence_lower": max(0, int(pred * 0.7)),
            "confidence_upper": int(pred * 1.3),
            "model_type": "baseline"
        })
    return results


def train_lstm_model(case_data: List[int], epochs: int = 50, lr: float = 0.001):
    """
    Train LSTM model on historical case data.
    Call this periodically to update the model.
    """
    if not TORCH_AVAILABLE or len(case_data) < 30:
        logger.warning("Insufficient data or PyTorch unavailable for training")
        return None

    data = np.array(case_data, dtype=np.float32)
    mean_val, std_val = data.mean(), data.std() + 1e-8
    normalized = (data - mean_val) / std_val

    seq_length = 14
    X, y = [], []
    for i in range(len(normalized) - seq_length - 7):
        X.append(normalized[i:i + seq_length])
        y.append(normalized[i + seq_length:i + seq_length + 7])

    if len(X) < 5:
        return None

    X = torch.FloatTensor(np.array(X)).unsqueeze(-1)
    y = torch.FloatTensor(np.array(y))

    model = LSTMPredictor(input_size=1, hidden_size=64, num_layers=2, output_size=7)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        output = model(X)
        loss = criterion(output, y)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch + 1}/{epochs}, Loss: {loss.item():.6f}")

    return model
