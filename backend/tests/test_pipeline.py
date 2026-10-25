"""Exercise retrieval and consolidation with deterministic vectors and no API calls."""
import pytest

from src.core.brain import Brain
from src.core.memory import MemoryManager


class MockLLM:
    def __init__(self):
        self.compressed = False

    def generate_embeddings(self, texts):
        return [[0.0, 1.0] if 'new topic' in text else [1.0, 0.0] for text in texts]

    def generate_response(self, query, context, history, session_history=None):
        return 'Mock answer'

    def synthesize_session(self, log_history, context_html):
        return '<section><p>Consolidated memory.</p></section>'

    def generate_structured_html(self, raw_text, compress=False):
        self.compressed = compress
        return '<html><body><main id="root"><p>Reorganized memory.</p></main></body></html>'


@pytest.fixture
def brain(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return Brain(MemoryManager(), MockLLM())


def test_chat_buffers_and_consolidates_on_drift(brain, monkeypatch):
    assert brain.run_inference('First topic') == 'Mock answer'
    keyword_queries = []
    monkeypatch.setattr(brain.memory, 'keyword_search', lambda query: keyword_queries.append(query) or [])
    brain.run_inference('new topic')
    assert 'Consolidated memory.' in brain.memory.soup.get_text()
    assert [turn['query'] for turn in brain.engram_trace._get_stage_log()] == ['new topic']
    assert keyword_queries == ['new topic']
    assert len(brain.engram_trace._get_session_log()) == 2


def test_no_memorize_skips_stage_but_keeps_session(brain):
    brain.run_inference('First topic', no_memorize=True)
    assert brain.engram_trace._get_stage_log() == []
    assert len(brain.engram_trace._get_session_log()) == 1


def test_no_search_skips_both_retrievers(brain, monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail('Retrieval should be disabled')
    monkeypatch.setattr(brain.memory, 'semantic_search', fail)
    monkeypatch.setattr(brain.memory, 'keyword_search', fail)
    assert brain.run_inference('First topic', no_search=True) == 'Mock answer'


def test_sessions_keep_separate_logs(brain):
    brain.run_inference('First topic')
    brain.engram_trace.set_session('second')
    assert brain.engram_trace._get_stage_log() == []
    brain.run_inference('Second session')
    brain.engram_trace.set_session('default')
    assert [turn['query'] for turn in brain.engram_trace._get_session_log()] == ['First topic']


def test_api_chat_and_memory_lifecycle(brain, monkeypatch):
    """Smoke-test the public routes without credentials or external requests."""
    import sys
    from fastapi.testclient import TestClient

    monkeypatch.setattr('src.llm.langchain_client.LangChainClient', MockLLM)
    original_stdout = sys.stdout
    try:
        from main import app
        with TestClient(app) as client:
            assert client.get('/state').status_code == 200
            assert client.get('/sessions').json()['active_session'] == 'default'
            response = client.post('/chat', json={'query': 'First topic'})
            assert response.status_code == 200
            assert response.json()['response'] == 'Mock answer'
            assert client.get('/state').json()['session_log'][0]['query'] == 'First topic'
            assert client.post('/day-change').json()['status'] == 'success'
            assert client.get('/openapi.json').status_code == 200
    finally:
        sys.stdout = original_stdout
