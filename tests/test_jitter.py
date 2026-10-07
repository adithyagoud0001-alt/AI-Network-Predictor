"""Unit tests for Network Jitter Calculations (RFC 3550, MAPDV, Standard Deviation)."""

import math
import pytest
import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.collector.jitter import JitterCalculator


def test_jitter_empty_and_single_sample():
    """Edge cases: empty lists or single samples should return 0.0 without errors."""
    assert JitterCalculator.calculate_rfc3550_jitter([]) == 0.0
    assert JitterCalculator.calculate_rfc3550_jitter([15.0]) == 0.0
    assert JitterCalculator.calculate_mean_pdv([]) == 0.0
    assert JitterCalculator.calculate_mean_pdv([15.0]) == 0.0
    assert JitterCalculator.calculate_std_jitter([]) == 0.0
    assert JitterCalculator.calculate_std_jitter([15.0]) == 0.0


def test_jitter_constant_delay():
    """Constant latency should have zero jitter."""
    delays = [20.0, 20.0, 20.0, 20.0, 20.0]
    assert JitterCalculator.calculate_rfc3550_jitter(delays) == 0.0
    assert JitterCalculator.calculate_mean_pdv(delays) == 0.0
    assert JitterCalculator.calculate_std_jitter(delays) == 0.0


def test_mean_pdv_calculation():
    """Verifies MAPDV on known sequence: [10, 20, 10, 30].
    Differences:
    |20 - 10| = 10
    |10 - 20| = 10
    |30 - 10| = 20
    Mean = (10 + 10 + 20) / 3 = 40 / 3 = 13.333
    """
    delays = [10.0, 20.0, 10.0, 30.0]
    mapdv = JitterCalculator.calculate_mean_pdv(delays)
    assert mapdv == 13.333


def test_rfc3550_jitter_formula():
    """Verifies RFC 3550 formula step-by-step:
    delays = [10, 26]
    D(0, 1) = 16
    J(1) = 0 + (16 - 0) / 16 = 1.0
    """
    delays = [10.0, 26.0]
    rfc_j = JitterCalculator.calculate_rfc3550_jitter(delays)
    assert rfc_j == 1.0


def test_jitter_handles_none_and_nan():
    """Checks handling of missing/NaN samples in sequence."""
    delays = [10.0, None, 20.0, float("nan"), 10.0]
    # Filtered valid delays should be [10.0, 20.0, 10.0]
    # Diffs: |20 - 10| = 10, |10 - 20| = 10 -> MAPDV = 10.0
    mapdv = JitterCalculator.calculate_mean_pdv(delays)
    assert mapdv == 10.0
