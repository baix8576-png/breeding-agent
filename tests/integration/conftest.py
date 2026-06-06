from __future__ import annotations

import pytest

from runtime.settings import get_settings


@pytest.fixture(autouse=True)
def isolate_local_state_root(tmp_path, monkeypatch):
    monkeypatch.setenv("GENEAGENT_LOCAL_STATE_ROOT", str(tmp_path / ".geneagent_state"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
