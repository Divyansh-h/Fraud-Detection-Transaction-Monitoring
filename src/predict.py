"""Inference and Scoring Module for Production Transaction Monitoring.

Provides the canonical score_dataframe(df) function that loads the persisted final
Isolation Forest model and metadata, constructs features via build_features(), verifies
feature alignment, and returns continuous anomaly scores and binary alert flags.
"""

from pathlib import Path
import json
import sys
from typing import Any, NamedTuple, Optional, Union

import joblib
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.features import build_features

# Module-level cache for fast repeated scoring
_CACHED_MODEL: Optional[Any] = None
_CACHED_METADATA: Optional[dict[str, Any]] = None


class PredictionOutput(tuple):
    """Container for model prediction outputs.

    Inherits from tuple to support standard tuple unpacking:
        scores, flags = score_dataframe(df)
    while also providing named attribute and dictionary-style key access:
        res.anomaly_score, res.ml_flag
        res['anomaly_score'], res['ml_flag']
    """

    def __new__(cls, anomaly_score: np.ndarray, ml_flag: np.ndarray):
        return super().__new__(cls, (anomaly_score, ml_flag))

    @property
    def anomaly_score(self) -> np.ndarray:
        """Continuous anomaly scores (higher value = higher fraud risk)."""
        return self[0]

    @property
    def ml_flag(self) -> np.ndarray:
        """Binary anomaly alert flag using calibrated best_f1 threshold."""
        return self[1]

    def __getitem__(self, item: Any) -> Any:
        if item == "anomaly_score":
            return self[0]
        if item == "ml_flag":
            return self[1]
        return super().__getitem__(item)


def load_model_and_metadata(
    model_path: Optional[Path] = None,
    metadata_path: Optional[Path] = None,
    force_reload: bool = False,
) -> tuple[Any, dict[str, Any]]:
    """Load model artifact and metadata JSON from disk with caching.

    Args:
        model_path: Path to serialized IsolationForest joblib. Defaults to config.MODEL_FINAL_JOBLIB.
        metadata_path: Path to model_metadata.json. Defaults to config.MODEL_METADATA_JSON.
        force_reload: If True, bypasses cache and reloads from disk.

    Returns:
        tuple[Any, dict[str, Any]]: Loaded IsolationForest model and metadata dictionary.
    """
    global _CACHED_MODEL, _CACHED_METADATA

    if not force_reload and _CACHED_MODEL is not None and _CACHED_METADATA is not None:
        return _CACHED_MODEL, _CACHED_METADATA

    m_path = model_path or config.MODEL_FINAL_JOBLIB
    meta_path = metadata_path or config.MODEL_METADATA_JSON

    if not m_path.exists():
        raise FileNotFoundError(f"Model file not found at: {m_path}. Run src/final_model.py first.")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found at: {meta_path}. Run src/final_model.py first.")

    model = joblib.load(m_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    _CACHED_MODEL = model
    _CACHED_METADATA = metadata
    return model, metadata


def score_dataframe(
    df: pd.DataFrame,
    threshold: Optional[float] = None,
) -> PredictionOutput:
    """Score a transaction DataFrame through feature generation and model inference.

    Loads the persisted model and metadata, transforms transactions via build_features(),
    verifies that feature columns strictly match metadata ordering, and computes
    continuous anomaly scores and binary alert flags.

    Args:
        df: Scoped DataFrame (or sample) containing transaction records.
        threshold: Optional custom decision threshold. If None, uses best_f1 from metadata.

    Returns:
        PredictionOutput: Tuple of (anomaly_score, ml_flag) with attribute and dict access.
    """
    model, metadata = load_model_and_metadata()

    # 1. Feature Engineering via build_features()
    feature_df = build_features(df)

    # 2. Verify feature columns and ordering strictly match metadata
    expected_columns = metadata.get("feature_columns") or metadata.get("FEATURE_COLUMNS")
    actual_columns = list(feature_df.columns)

    assert actual_columns == expected_columns, (
        f"Feature alignment error!\nExpected: {expected_columns}\nActual:   {actual_columns}"
    )

    # 3. Model Inference (Isolation Forest returns negative scores; invert for positive risk scale)
    anomaly_scores = -model.score_samples(feature_df[expected_columns])

    # 4. Binary Alert Flagging
    if threshold is None:
        best_f1_threshold = float(metadata["thresholds"]["best_f1"])
    else:
        best_f1_threshold = float(threshold)

    ml_flags = (anomaly_scores >= best_f1_threshold).astype(np.int8)

    return PredictionOutput(anomaly_scores, ml_flags)
