import logging
import math
from collections import deque
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class SignalProcessor:
    """
    Processes and analyzes time-series signal data.
    """

    def __init__(
        self,
        history_size: int = 1000,
        spike_factor: float = 3.0,
        stability_tolerance: float = 0.1,
        strong_threshold: float = 0.75,
    ):
        # Store recent signal values with timestamps
        self.history: deque[Tuple[datetime, float]] = deque(maxlen=history_size)
        self.spike_factor = spike_factor
        self.stability_tolerance = stability_tolerance
        self.strong_threshold = strong_threshold

    def normalize(self, values: List[float]) -> List[float]:
        """
        Scale a list of values to the range [0, 1].
        """
        if not values:
            return []
        min_v, max_v = min(values), max(values)
        span = max_v - min_v or 1e-6
        return [(v - min_v) / span for v in values]

    def moving_average(self, data: List[float], window: int) -> List[float]:
        """
        Compute simple moving average with specified window size.
        """
        if window <= 0 or window > len(data):
            return []
        return [
            sum(data[i : i + window]) / window
            for i in range(len(data) - window + 1)
        ]

    def volatility(self, data: List[float]) -> float:
        """
        Calculate variance (volatility) of the data.
        """
        n = len(data)
        if n == 0:
            return 0.0
        mean = sum(data) / n
        return sum((x - mean) ** 2 for x in data) / n

    def detect_spike(self, data: List[float]) -> bool:
        """
        Detect a sudden spike if the last change exceeds
        average change by a configured factor.
        """
        if len(data) < 3:
            return False
        diffs = [abs(data[i] - data[i - 1]) for i in range(1, len(data))]
        avg_diff = sum(diffs) / len(diffs)
        return diffs[-1] > avg_diff * self.spike_factor

    def store_signal(self, value: float) -> None:
        """
        Append a new signal value with current UTC timestamp.
        """
        self.history.append((datetime.utcnow(), value))

    def get_recent_signals(self, seconds: int = 60) -> List[float]:
        """
        Return all signal values recorded within the last N seconds.
        """
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        return [v for t, v in self.history if t >= cutoff]

    def score_signal(self, values: List[float]) -> float:
        """
        Compute a score: the average of normalized values
        reduced by their volatility component.
        """
        norm = self.normalize(values)
        if not norm:
            return 0.0
        avg = sum(norm) / len(norm)
        vol = self.volatility(norm)
        score = avg * (1 - vol)
        return max(0.0, min(score, 1.0))

    def classify_signal(self, score: float) -> str:
        """
        Categorize the signal strength based on thresholds.
        """
        if score > self.strong_threshold:
            return "Strong"
        if score > self.strong_threshold / 2:
            return "Moderate"
        return "Weak"

    def resample(self, data: List[float], factor: int) -> List[float]:
        """
        Downsample data by averaging every 'factor' elements.
        """
        if factor <= 1:
            return data.copy()
        return [
            sum(chunk) / len(chunk)
            for i in range(0, len(data), factor)
            if (chunk := data[i : i + factor])
        ]

    def interpolate_missing(self, data: List[Optional[float]]) -> List[float]:
        """
        Linearly interpolate None values between neighbors.
        """
        filled: List[float] = []
        for i, v in enumerate(data):
            if v is None and 0 < i < len(data) - 1:
                filled.append((data[i - 1] + data[i + 1]) / 2)  # type: ignore
            else:
                filled.append(v or 0.0)
        return filled

    def smooth(self, data: List[float]) -> List[float]:
        """
        Apply a window-3 moving average for smoothing.
        """
        return self.moving_average(data, window=3)

    def trend(self, data: List[float]) -> str:
        """
        Identify overall trend: 'upward', 'downward', or 'flat'.
        """
        if len(data) < 2:
            return "flat"
        return "upward" if data[-1] > data[0] else "downward"

    def detect_anomaly(self, value: float, reference: float) -> bool:
        """
        Flag an anomaly if deviation exceeds 2 * sqrt(reference).
        """
        return abs(value - reference) > 2 * math.sqrt(reference or 1)

    def group_by_threshold(
        self, data: List[float], threshold: float
    ) -> Tuple[List[float], List[float]]:
        """
        Split data into values above and at/below a threshold.
        """
        above = [x for x in data if x > threshold]
        below = [x for x in data if x <= threshold]
        return above, below

    def sync_timestamps(self, times: List[datetime]) -> List[float]:
        """
        Convert datetime list to elapsed seconds from first timestamp.
        """
        base = times[0] if times else datetime.utcnow()
        return [(t - base).total_seconds() for t in times]

    def trend_consistency(self, data: List[float]) -> float:
        """
        Compute the fraction of successive steps that share the same sign.
        """
        if len(data) < 2:
            return 1.0
        diffs = [data[i + 1] - data[i] for i in range(len(data) - 1)]
        signs = [1 if d > 0 else -1 for d in diffs]
        return sum(signs) / len(signs)

    def collapse_outliers(self, data: List[float], multiplier: float = 1.5) -> List[float]:
        """
        Remove outliers outside the IQR-based fence.
        """
        if not data:
            return []
        sorted_d = sorted(data)
        n = len(data)
        q1, q3 = sorted_d[n // 4], sorted_d[3 * n // 4]
        iqr = q3 - q1
        low, high = q1 - multiplier * iqr, q3 + multiplier * iqr
        return [x for x in data if low <= x <= high]

    def is_stable(self, data: List[float]) -> bool:
        """
        Check if relative volatility (variance/mean) is within tolerance.
        """
        if not data:
            return True
        vol = self.volatility(data)
        avg = sum(data) / len(data)
        return (vol / (avg or 1)) < self.stability_tolerance


# Example usage
if __name__ == "__main__":
    import random

    processor = SignalProcessor()
    sample_data = [random.random() for _ in range(100)]
    processor.store_signal(sample_data[-1])
    recent_values = processor.get_recent_signals(3600)
    score = processor.score_signal(sample_data)
    classification = processor.classify_signal(score)
    logger.info("Signal score=%.3f, classification=%s", score, classification)
