"""Session-wide fixtures for NJM OS backend tests."""
import asyncio
import os

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test")


@pytest.fixture(autouse=True, scope="session")
def _init_njm_graph():
    """Initialize njm_graph once per test session so monkeypatching works."""
    from agent.njm_graph import init_graph
    asyncio.run(init_graph())
