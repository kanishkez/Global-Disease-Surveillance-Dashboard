"""Anomaly Detection for Disease Case Spikes"""
import numpy as np
import logging
from typing import List, Dict, Optional
from datetime import date, timedelta

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, using statistical anomaly detection")


class AnomalyDetector:
    """Detect anomalous spikes in disease case data using Isolation Forest."""

    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.model = None
        self.scaler = None

    def fit(self, case_data: List[int]):
        """Fit the anomaly detector on historical case data."""
        if len(case_data) < 10:
            logger.warning("Insufficient data for anomaly detection training")
            return

        data = np.array(case_data, dtype=np.float64).reshape(-1, 1)

        if SKLEARN_AVAILABLE:
            self.scaler = StandardScaler()
            scaled_data = self.scaler.fit_transform(data)

            self.model = IsolationForest(
                contamination=self.contamination,
                n_estimators=100,
                random_state=42
            )
            self.model.fit(scaled_data)
            logger.info("Anomaly detection model fitted successfully")
        else:
            # Store statistics for fallback
            self._mean = np.mean(data)
            self._std = np.std(data)

    def detect(self, case_data: List[int]) -> List[Dict]:
        """
        Detect anomalies in case data.
        
        Returns:
            List of dictionaries with index, value, is_anomaly, anomaly_score
        """
        if len(case_data) < 3:
            return []

        if self.model and SKLEARN_AVAILABLE:
            return self._isolation_forest_detect(case_data)

        return self._statistical_detect(case_data)

    def _isolation_forest_detect(self, case_data: List[int]) -> List[Dict]:
        """Use Isolation Forest for anomaly detection."""
        data = np.array(case_data, dtype=np.float64).reshape(-1, 1)

        if self.scaler is None:
            self.scaler = StandardScaler()
            scaled = self.scaler.fit_transform(data)
        else:
            scaled = self.scaler.transform(data)

        if self.model is None:
            self.fit(case_data)

        if self.model is None:
            return self._statistical_detect(case_data)

        predictions = self.model.predict(scaled)
        scores = self.model.decision_function(scaled)

        # Normalize scores to 0-1 range (lower = more anomalous)
        min_score = scores.min()
        max_score = scores.max()
        score_range = max_score - min_score + 1e-8
        normalized_scores = 1 - (scores - min_score) / score_range

        results = []
        today = date.today()
        for i, (value, pred, score) in enumerate(zip(case_data, predictions, normalized_scores)):
            day = today - timedelta(days=len(case_data) - i - 1)
            results.append({
                "date": day.isoformat(),
                "value": int(value),
                "is_anomaly": bool(pred == -1),
                "anomaly_score": round(float(score), 4)
            })

        return results

    def _statistical_detect(self, case_data: List[int]) -> List[Dict]:
        """Statistical fallback: Z-score based anomaly detection."""
        data = np.array(case_data, dtype=np.float64)
        mean = np.mean(data)
        std = np.std(data) + 1e-8

        # Calculate rolling statistics for more robust detection
        window = min(7, len(data) // 2)
        results = []
        today = date.today()

        for i in range(len(data)):
            # Use local context for anomaly detection
            start = max(0, i - window)
            local_data = data[start:i] if i > 0 else data[:1]
            local_mean = np.mean(local_data) if len(local_data) > 0 else mean
            local_std = np.std(local_data) if len(local_data) > 1 else std

            z_score = abs(data[i] - local_mean) / (local_std + 1e-8)

            # Also check rate of change
            change_rate = 0
            if i > 0 and data[i - 1] > 0:
                change_rate = (data[i] - data[i - 1]) / data[i - 1]

            is_anomaly = z_score > 2.5 or change_rate > 2.0
            anomaly_score = min(1.0, z_score / 5.0)

            day = today - timedelta(days=len(data) - i - 1)
            results.append({
                "date": day.isoformat(),
                "value": int(data[i]),
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": round(anomaly_score, 4)
            })

        return results


def detect_anomalies(case_data: List[int], contamination: float = 0.1) -> List[Dict]:
    """Convenience function for anomaly detection."""
    detector = AnomalyDetector(contamination=contamination)
    detector.fit(case_data)
    return detector.detect(case_data)


def get_anomaly_summary(results: List[Dict]) -> Dict:
    """Summarize anomaly detection results."""
    anomalies = [r for r in results if r["is_anomaly"]]
    return {
        "total_points": len(results),
        "anomaly_count": len(anomalies),
        "anomaly_rate": round(len(anomalies) / max(len(results), 1), 3),
        "max_anomaly_score": max((r["anomaly_score"] for r in results), default=0),
        "anomalous_dates": [r["date"] for r in anomalies],
        "anomalous_values": [r["value"] for r in anomalies]
    }
