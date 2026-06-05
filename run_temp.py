import main
from pathlib import Path
from src.chunking import FixedSizeChunker
from src.agent import KnowledgeBaseAgent
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore

files = [str(file) for file in Path('data/Company Policies').iterdir() if file.is_file()]
raw_docs = main.load_documents_from_files(files)
chunker = FixedSizeChunker(chunk_size=500, overlap=50)
docs = []
for doc in raw_docs:
    chunks = chunker.chunk(doc.content)
    for i, c in enumerate(chunks):
        docs.append(Document(id=f'{doc.id}_chunk{i}', content=c, metadata=doc.metadata))

store = EmbeddingStore(collection_name='manual_test_store_fixed', embedding_fn=_mock_embed)
store.add_documents(docs)
agent = KnowledgeBaseAgent(store=store, llm_fn=main.demo_llm)

queries = [
    'How long can I work remotely before needing manager approval?',
    'How many vacation days do I accrue each month?',
    'How long is the New Parent Leave policy for birth or adoption?',
    'What is the salary for a technical employee with less than 5 years of experience?',
    'Who should I contact if I notice harassment in the company?'
]

expected_docs = [
    'Working Remotely',
    'Vacation and Sick Leave',
    'New Parent Leave',
    'Salary and Equity Compensation',
    'Code of Conduct in the Community'
]

relevant_count = 0
for i, q in enumerate(queries, 1):
    search_results = store.search(q, top_k=3)
    top1 = search_results[0]
    score = top1['score']
    is_relevant = False
    for res in search_results:
        if expected_docs[i-1] in res['metadata'].get('source', ''):
            is_relevant = True
            break
    if is_relevant: relevant_count += 1
    rel_str = 'Có' if is_relevant else 'Không'
    chunk_preview = top1['content'][:60].replace('\n', ' ').replace('\r', ' ') + '...'
    answer = agent.answer(q, top_k=3).split("Context: ")[1]
#    if len(answer) > 80: answer = answer[:77].replace('\n', ' ').replace('\r', ' ') + '...'
    print(f'| {i} | {q} | "{chunk_preview}" | {score:.3f} | {rel_str} | {answer} |')

print(f'\n**Bao nhiêu queries trả về chunk relevant trong top-3?** {relevant_count} / 5')
