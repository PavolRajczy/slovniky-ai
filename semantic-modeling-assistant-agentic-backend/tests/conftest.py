import os

import pytest

LIVE_TESTS_ENV_VAR = "RUN_LIVE_TESTS"


def pytest_collection_modifyitems(config, items):
    if os.getenv(LIVE_TESTS_ENV_VAR) == "1":
        return
    skip_live = pytest.mark.skip(
        reason=f"needs e-Sbírka or the LLM API; set {LIVE_TESTS_ENV_VAR}=1 to run"
    )
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
