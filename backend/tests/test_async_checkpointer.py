import os
os.environ.setdefault("OPENAI_API_KEY", "test")

def test_njm_graph_has_async_checkpointer():
    """njm_graph checkpointer must be AsyncSqliteSaver."""
    from agent.njm_graph import njm_graph
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    assert isinstance(njm_graph.checkpointer, AsyncSqliteSaver)
