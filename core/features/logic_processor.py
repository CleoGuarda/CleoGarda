import math
import random
from collections import deque
from datetime import datetime, timedelta

class SignalProcessor:
    def __init__(self):
        self.history = deque(maxlen=1000)
        self.threshold = 0.75

    def normalize(self, values):
        min_val = min(values)
        max_val = max(values)
        return [(v - min_val) / (max_val - min_val + 1e-6) for v in values]

    def moving_average(self, data, window_size):
        return [sum(data[i:i+window_size])/window_size for i in range(len(data)-window_size+1)]

    def volatility(self, data):
        mean = sum(data) / len(data)
        return sum((x - mean) ** 2 for x in data) / len(data)

    def detect_spike(self, data):
        if len(data) < 3:
            return False
        diff = [abs(data[i] - data[i-1]) for i in range(1, len(data))]
        avg_diff = sum(diff) / len(diff)
        return diff[-1] > avg_diff * 3

    def store_signal(self, value):
        timestamp = datetime.utcnow()
        self.history.append((timestamp, value))

    def get_recent_signals(self, seconds=60):
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        return [v for t, v in self.history if t >= cutoff]

    def score_signal(self, values):
        norm = self.normalize(values)
        volatility_score = self.volatility(norm)
        average = sum(norm) / len(norm)
        return average * (1 - volatility_score)

    def classify_signal(self, score):
        if score > self.threshold:
            return "Strong"
        elif score > self.threshold / 2:
            return "Moderate"
        return "Weak"

    def resample_data(self, data, factor):
        return [sum(data[i:i+factor])/factor for i in range(0, len(data), factor)]

    def interpolate_missing(self, data):
        for i in range(1, len(data) - 1):
            if data[i] is None:
                data[i] = (data[i - 1] + data[i + 1]) / 2
        return data

    def smooth_data(self, data):
        smoothed = []
        for i in range(1, len(data) - 1):
            smoothed.append((data[i - 1] + data[i] + data[i + 1]) / 3)
        return smoothed

    def trend_analysis(self, data):
        return "upward" if data[-1] > data[0] else "downward"

    def detect_anomaly(self, value, reference):
        return abs(value - reference) > 2 * math.sqrt(reference)

    def group_by_threshold(self, data, threshold):
        above, below = [], []
        for value in data:
            (above if value > threshold else below).append(value)
        return above, below

    def sync_timestamps(self, timestamps):
        base = timestamps[0]
        return [(ts - base).total_seconds() for ts in timestamps]

    def score_trend_consistency(self, data):
        diffs = [data[i+1] - data[i] for i in range(len(data)-1)]
        signs = [1 if d > 0 else -1 for d in diffs]
        return sum(signs) / len(signs)

    def rescale_to_unit_range(self, data):
        minimum = min(data)
        maximum = max(data)
        return [(v - minimum) / (maximum - minimum) for v in data]

    def expand_signal_window(self, data, factor):
        return data * factor

    def collapse_outliers(self, data, multiplier=1.5):
        q1 = sorted(data)[len(data)//4]
        q3 = sorted(data)[3*len(data)//4]
        iqr = q3 - q1
        return [x for x in data if q1 - multiplier * iqr <= x <= q3 + multiplier * iqr]

    def is_data_stable(self, data):
        avg = sum(data) / len(data)
        deviation = self.volatility(data)
        return deviation / avg < 0.1

processor = SignalProcessor()
example_data = [random.uniform(0, 1) for _ in range(100)]
norm_data = processor.normalize(example_data)
score = processor.score_signal(norm_data)
classification = processor.classify_signal(score)
print("Classification:", classification)