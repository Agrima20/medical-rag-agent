# This file manages the ChromaDB vector database
# Vector databases store text as mathematical vectors (embeddings)
# This lets us find semantically similar text — not just keyword matching
# e.g. "heart attack" will match "myocardial infarction" because they mean the same thing

import chromadb
from sentence_transformers import SentenceTransformer

# Load a free, lightweight embedding model that runs fully locally (no API needed)
# all-MiniLM-L6-v2 is fast, small, and works well for medical/scientific text
# It converts text into 384-dimensional vectors
EMBED_MODEL = SentenceTransformer("NeuML/pubmedbert-base-embeddings")

# Create a persistent ChromaDB client
# PersistentClient saves the database to disk so data survives restarts
# All your indexed papers will be saved in the ./chroma_db folder
client = chromadb.PersistentClient(path="./chroma_db")

# Create or load a collection (like a table in a regular database)
# All medical papers — both from PubMed and uploaded PDFs — go into one collection
collection = client.get_or_create_collection("medical_papers")


def add_documents(docs: list):
    """
    Embed and store a list of document chunks into ChromaDB.
    
    Args:
        docs: List of dicts with 'text' and metadata fields
    """

    # Extract just the text content for embedding
    texts = [d["text"] for d in docs]

    # Convert text chunks into vectors using the embedding model
    # This is the core of semantic search — similar meaning = similar vector
    embeddings = EMBED_MODEL.encode(texts).tolist()

    # Create unique IDs for each chunk
    # Using PMID or filename + index ensures no duplicates
    ids = [
        f"{d.get('pmid', d.get('source', 'doc'))}_{i}"
        for i, d in enumerate(docs)
    ]

    # Extract metadata (everything except the text itself)
    # Metadata is stored alongside vectors and returned with search results
    metadatas = [
        {k: v for k, v in d.items() if k != "text"}
        for d in docs
    ]

    # Store everything in ChromaDB
    collection.add(
        documents=texts,        # original text (stored for display)
        embeddings=embeddings,  # vector representations (used for search)
        metadatas=metadatas,    # citation info (journal, doi, year etc.)
        ids=ids                 # unique identifiers
    )


def retrieve(query: str, top_k: int = 5, filter_source: str = None) -> list:
    """
    Find the most relevant document chunks for a given query.
    
    Args:
        query: The user's medical question
        top_k: How many chunks to retrieve (default 5)
        filter_source: "pdf" to only return uploaded PDF chunks, None for all
    
    Returns:
        List of relevant chunks with text and metadata
    """

    q_embedding = EMBED_MODEL.encode([query]).tolist()

    # If uploaded only mode — filter ChromaDB to only return PDF chunks
    # Uploaded PDFs are tagged with "Uploaded PDF: filename" in their doi field
    if filter_source == "pdf":
        try:
            results = collection.query(
                query_embeddings=q_embedding,
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
                where={"doi": {"$contains": "Uploaded PDF"}}
            )
        except Exception as e:
            # If no PDFs uploaded yet, ChromaDB throws an error
            # Return empty list gracefully
            print(f"PDF filter error (no PDFs uploaded yet?): {e}")
            return []
    else:
        results = collection.query(
            query_embeddings=q_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        if dist < 350:
            chunks.append({
                "text":     doc,
                "meta":     meta,
                "distance": dist
            })

    return chunks