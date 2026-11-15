"""The CSV generator is reproducible: seed and start date fix every row."""

import importlib.util
import random
from datetime import date
from pathlib import Path

import pandas as pd

DATASET_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_dataset.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_dataset", DATASET_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_same_seed_gives_the_same_dataset():
    module = _load_module()

    first = module.generate_dataset(days=30, seed=7)
    random.seed(12345)  # the global generator must not matter
    second = module.generate_dataset(days=30, seed=7)

    pd.testing.assert_frame_equal(first, second)


def test_another_seed_gives_another_dataset():
    module = _load_module()

    assert not module.generate_dataset(days=30, seed=7).equals(module.generate_dataset(days=30, seed=8))


def test_dates_start_on_the_fixed_day_not_today():
    module = _load_module()

    frame = module.generate_dataset(days=3)

    assert frame["fecha"].str[:10].min() == module.START_DATE.isoformat()
    assert frame["fecha"].str[:10].max() == "2023-11-03"


def test_start_date_can_be_chosen():
    module = _load_module()

    frame = module.generate_dataset(days=1, start=date(2025, 2, 1))

    assert set(frame["fecha"].str[:10]) == {"2025-02-01"}
