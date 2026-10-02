"""
Metrics collection for provider attempts.
"""

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict

from config import settings


class MetricsCollector:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.storage_path = getattr(settings, "METRICS_STORAGE_PATH", "./data/metrics.jsonl")
        self.flush_interval = getattr(settings, "METRICS_FLUSH_INTERVAL", 5.0)
        self._buffer = []
        self._last_flush = time.time()
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        # Start a background thread for periodic flush if flush_interval > 0
        if self.flush_interval > 0:
            self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
            self._flush_thread.start()

    def _flush_loop(self):
        while True:
            time.sleep(self.flush_interval)
            self.flush()

    def record_attempt(self, metrics: Dict[str, Any]) -> None:
        """
        Record a single attempt metric.
        :param metrics: Dictionary with keys:
            - timestamp (ISO 8601 string)
            - request_id (str)
            - provider (str)
            - model (str)
            - input_tokens (int or None)
            - output_tokens (int or None)
            - total_tokens (int or None, or compute if both present)
            - duration_ms (float or int)
            - success (bool)
            - error_category (str or None)
        """
        # Ensure total_tokens is present if possible
        if metrics.get("total_tokens") is None:
            input_tokens = metrics.get("input_tokens")
            output_tokens = metrics.get("output_tokens")
            if input_tokens is not None and output_tokens is not None:
                metrics["total_tokens"] = input_tokens + output_tokens
        # Add a timestamp if not provided (should be, but just in case)
        if "timestamp" not in metrics:
            metrics["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._buffer.append(metrics)
        # Flush if buffer is large enough or time elapsed (simple heuristic)
        if len(self._buffer) >= 100 or (time.time() - self._last_flush) >= self.flush_interval:
            self.flush()

    def flush(self) -> None:
        """Write buffered metrics to disk."""
        if not self._buffer:
            return
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                for metrics in self._buffer:
                    f.write(json.dumps(metrics, ensure_ascii=False) + "\n")
            self._buffer.clear()
            self._last_flush = time.time()
        except Exception:
            # Log but do not raise; we don't want to break the request flow
            # In a real system, we might use a logger, but to avoid circular deps, we print.
            # However, we have access to logger via importing? Let's avoid and just ignore.
            # In production, we would want to log this, but for now we suppress.
            pass

    def shutdown(self):
        """Flush any remaining metrics and stop background thread."""
        self.flush()
        # Note: The daemon thread will exit when the main thread exits.


# Singleton instance
metrics_collector = MetricsCollector()


def record_attempt(metrics: Dict[str, Any]) -> None:
    """
    Public function to record a metrics attempt.
    """
    metrics_collector.record_attempt(metrics)
