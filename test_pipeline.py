from agent.pubmed_search import search_pubmed
from agent.vectorstore import add_documents, retrieve, collection

query = "metformin side effects"

# Step 1 - fetch from pubmed
print("=== STEP 1: PubMed Search ===")
papers = search_pubmed(query, max_results=3)
print(f"Papers fetched: {len(papers)}")

# Step 2 - add to chromadb
print("\n=== STEP 2: Adding to ChromaDB ===")
docs = [{
    "text": f"{p['title']}. {p['abstract']}",
    "pmid": p["pmid"],
    "source": p["journal"],
    "doi": p["doi"],
    "year": p["year"]
} for p in papers]

print(f"Docs prepared: {len(docs)}")
print(f"Sample text (first 200 chars): {docs[0]['text'][:200]}")

add_documents(docs)
print("Documents added successfully")

# Step 3 - check collection count
print(f"\n=== STEP 3: Collection Count ===")
print(f"Total docs in ChromaDB: {collection.count()}")

# Step 4 - retrieve
print(f"\n=== STEP 4: Retrieval ===")
results = retrieve(query, top_k=5)
print(f"Chunks retrieved: {len(results)}")
if results:
    for r in results:
        print(f"Distance: {r['distance']} | Source: {r['meta'].get('source')}")
else:
    print("NO CHUNKS RETRIEVED - printing raw query results...")
    from agent.vectorstore import EMBED_MODEL
    q_embedding = EMBED_MODEL.encode([query]).tolist()
    raw = collection.query(query_embeddings=q_embedding, n_results=5, include=["documents","metadatas","distances"])
    print(f"Raw distances: {raw['distances']}")