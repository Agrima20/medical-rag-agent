from agent.vectorstore import EMBED_MODEL, collection, add_documents
from agent.pubmed_search import search_pubmed

query = "latest research on lungs"

# First add some papers
papers = search_pubmed(query, max_results=3)
docs = [{
    "text": f"{p['title']}. {p['abstract']}",
    "source": p["journal"],
    "doi": p["doi"],
    "year": p["year"]
} for p in papers]
add_documents(docs)

# Now check raw distances
q_embedding = EMBED_MODEL.encode([query]).tolist()
results = collection.query(
    query_embeddings=q_embedding,
    n_results=5,
    include=["documents", "metadatas", "distances"]
)

print("Raw distances:")
for dist in results["distances"][0]:
    print(f"  {dist}")