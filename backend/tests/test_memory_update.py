import json

import pytest

from src.core.memory import MemoryManager


class MockLLMClient:
    def generate_structured_html(self, raw_text, compress=False):
        return (
            "<html><body><main id='root'><section id='sec-1'>"
            "<p id='p-1'>Text 1</p><p id='p-2'>Text 2</p>"
            "</section></main></body></html>"
        )

    def generate_embeddings(self, texts):
        return [[0.1, 0.2] for _ in texts]


@pytest.fixture
def mem_and_llm(tmp_path):
    mem = MemoryManager(
        kb_path=str(tmp_path / 'kb.html'),
        p_embeddings_path=str(tmp_path / 'paragraphs.json'),
        structural_embeddings_path=str(tmp_path / 'structure.json'),
    )
    return mem, MockLLMClient()


def test_atomizer_assigns_stable_ids(mem_and_llm):
    mem, llm = mem_and_llm
    assert mem.atomizer(llm, raw_text='Test') == ['p-1', 'p-2']
    html = '<section><p>A new concept.</p></section>'
    first = mem.finalize_atomization(html)
    assert first == mem.finalize_atomization(html)
    assert 'p-' in first


def test_hierarchical_embedding_schema(mem_and_llm):
    mem, llm = mem_and_llm
    mem.atomizer(llm, raw_text='Test')
    data = json.loads(open(mem.p_embeddings_path).read())
    assert set(data) == {'p-1', 'p-2'}
    assert data['p-1']['selector'] == 'html > body > main#root > section#sec-1 > p#p-1'
    assert data['p-1']['vector'] == pytest.approx([0.1, 0.2])
    assert data['p-1']['last_consolidated']
    assert 'sec-1' in json.loads(open(mem.structural_embeddings_path).read())


def test_sync_prunes_deleted_paragraphs(mem_and_llm):
    mem, llm = mem_and_llm
    mem.atomizer(llm, raw_text='Test')
    mem.soup.find(id='p-1').decompose()
    mem.save_kb(str(mem.soup))
    mem.sync_embeddings(llm, ['p-2'])
    assert set(json.loads(open(mem.p_embeddings_path).read())) == {'p-2'}


def test_search_falls_back_to_nearest_nodes(mem_and_llm):
    mem, llm = mem_and_llm
    mem.atomizer(llm, raw_text='Test')
    assert set(mem.semantic_search([0.1, 0.2], threshold=1.1)) == {'p-1', 'p-2'}


def test_wipe_removes_indexes_and_resets_document(mem_and_llm):
    mem, llm = mem_and_llm
    mem.atomizer(llm, raw_text='Test')
    mem.wipe()
    assert not mem.soup.find_all('p')
    from pathlib import Path
    assert not Path(mem.p_embeddings_path).exists()
    assert not Path(mem.structural_embeddings_path).exists()
