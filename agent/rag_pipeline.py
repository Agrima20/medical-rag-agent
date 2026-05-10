import os
from groq import Groq
from dotenv import load_dotenv
from .pubmed_search import search_pubmed
from .europepmc_search import search_europepmc
from .openfda_search import search_openfda_label, search_openfda_adverse, is_drug_query
from .clinicaltrials_search import search_clinicaltrials
from .vectorstore import add_documents, retrieve

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# If any of these appear in the query we show an extra safety warning in the UI
HIGH_RISK_KEYWORDS = [
    "dose", "dosage", "how much", "overdose", "can i take",
    "should i take", "pregnancy", "pregnant", "child", "infant",
    "pediatric", "surgery", "diagnose", "diagnosis", "i have",
    "my patient", "treat me", "prescribe"
]

def is_high_risk(query: str) -> bool:
    """Check if query is asking for direct clinical advice"""
    return any(kw in query.lower() for kw in HIGH_RISK_KEYWORDS)


# ── Source tier labels ─────────────────────────────────────────────────────────
# Tier 1 = Regulatory/Guideline (FDA) — highest trust
# Tier 2 = Clinical Trial (NIH/ClinicalTrials.gov) — high trust
# Tier 3 = Peer reviewed research (PubMed, EuropePMC) — good trust
# Tier 4 = Uploaded PDF — trust depends on the document
def get_tier_label(source: str) -> str:
    if "FDA" in source or "Food and Drug" in source:
        return "Tier 1 — Official FDA Document"
    elif "ClinicalTrials" in source or "NIH" in source:
        return "Tier 2 — Clinical Trial (NIH)"
    elif "Uploaded PDF" in source:
        return "Tier 4 — Uploaded Document"
    else:
        return "Tier 3 — Peer Reviewed Research"


# This is the most critical part — instructs the LLM to NEVER hallucinate
# It must only use the context provided, nothing from its own training
SYSTEM_PROMPT = """You are a medical literature assistant for doctors and researchers.

YOUR STRICT RULES:
1. Answer ONLY using the [CONTEXT] provided below the question.
2. If the answer is not in the context say exactly:
   "This information was not found in the retrieved literature. Please consult additional sources."
3. NEVER use your own training knowledge to answer medical questions.
4. NEVER make up studies, statistics, or drug names.
5. Every factual claim MUST reference its source like this: (Source: Journal/Database, Year)
6. If two sources contradict each other, mention both and flag the contradiction clearly.
7. Structure your answer with clear sections when multiple aspects are covered.
8. Always recommend consulting a licensed medical professional for clinical decisions."""


# ── Main pipeline function ─────────────────────────────────────────────────────
def answer_query(user_query: str, search_mode: str = "all") -> dict:
    """
    Full multi-source RAG pipeline.
    
    Args:
        user_query:  The medical or research question from the user
        search_mode: "all"      = search all sources (PubMed, EuropePMC, FDA, ClinicalTrials)
                     "uploaded" = search only uploaded PDFs stored in ChromaDB
    
    Returns:
        Dict with:
            answer     — grounded answer from LLM
            sources    — list of cited sources with tier labels
            confidence — 0-100 score based on source diversity + chunk coverage + distance
            high_risk  — True if query involves dosage/diagnosis/clinical decisions
            tiers      — list of evidence tiers present in the answer
    """

    all_docs = []

    # Always initialize these so confidence scoring never throws NameError
    fda_labels    = []
    fda_adverse   = []
    pubmed_papers = []
    epmc_papers   = []
    trials        = []

    if search_mode == "all":

        # Source 1 — PubMed
        # 36M+ peer reviewed abstracts, free NCBI API
        print(f"[1/4] Searching PubMed...")
        pubmed_papers = search_pubmed(user_query, max_results=5)
        for p in pubmed_papers:
            all_docs.append({
                "text":   f"{p['title']}. {p['abstract']}",
                "source": p["journal"] or "PubMed",
                "doi":    p["doi"],
                "year":   p["year"],
                "tier":   "3"
            })
        print(f"    → {len(pubmed_papers)} papers found")

        # Source 2 — Europe PMC
        # 42M+ abstracts + 9M full text open access, WHO endorsed
        print(f"[2/4] Searching Europe PMC...")
        epmc_papers = search_europepmc(user_query, max_results=5)
        for p in epmc_papers:
            all_docs.append({
                "text":   f"{p['title']}. {p['abstract']}",
                "source": p["journal"] or "Europe PMC",
                "doi":    p["doi"],
                "year":   p["year"],
                "tier":   "3"
            })
        print(f"    → {len(epmc_papers)} papers found")

        # Source 3 — OpenFDA
        # Only triggered for drug-related queries
        # Returns official FDA drug labels + real world adverse event reports
        print(f"[3/4] Checking OpenFDA...")
        if is_drug_query(user_query):
            # Extract the drug name from the query
            # Simple heuristic: take the word after trigger words like "of", "for"
            words        = user_query.lower().split()
            drug_trigger = ["of", "for", "about", "with"]
            drug_name    = user_query  # fallback to full query if no trigger found
            for i, w in enumerate(words):
                if w in drug_trigger and i + 1 < len(words):
                    drug_name = words[i + 1]
                    break

            fda_labels  = search_openfda_label(drug_name)
            fda_adverse = search_openfda_adverse(drug_name)
            all_docs.extend(fda_labels)
            all_docs.extend(fda_adverse)
            print(f"    → {len(fda_labels)} FDA labels + {len(fda_adverse)} adverse reports")
        else:
            print(f"    → Skipped (not a drug query)")

        # Source 4 — ClinicalTrials.gov
        # Completed trials only — strongest human evidence
        print(f"[4/4] Searching ClinicalTrials.gov...")
        trials = search_clinicaltrials(user_query, max_results=3)
        all_docs.extend(trials)
        print(f"    → {len(trials)} trials found")

        # Add all fetched docs into ChromaDB for retrieval
        if all_docs:
            add_documents(all_docs)

    # ── Mode: Uploaded PDFs only ───────────────────────────────────────────────
    else:
        # Skip all live API calls
        # Only search what's already indexed in ChromaDB from uploaded PDFs
        print(f"[Uploaded only mode] Searching uploaded PDFs...")

    # ── Retrieve most relevant chunks from ChromaDB ────────────────────────────
    if search_mode == "uploaded":
        # Filter to only return chunks tagged as uploaded PDFs
        chunks = retrieve(
            user_query,
            top_k=6,
            filter_source="pdf"
        )
    else:
        # Return chunks from all sources
        chunks = retrieve(user_query, top_k=6)

    print(f"Retrieved {len(chunks)} relevant chunks")

    # ── No results handler ─────────────────────────────────────────────────────
    if not chunks:
        if search_mode == "uploaded":
            return {
                "answer":     "No relevant content found in your uploaded PDFs. "
                              "Please upload a relevant paper first, or switch to "
                              "'Search all sources' mode.",
                "sources":    [],
                "confidence": 0,
                "high_risk":  False,
                "tiers":      []
            }
        return {
            "answer":     "No relevant literature found for this query. "
                          "Try rephrasing or uploading related papers.",
            "sources":    [],
            "confidence": 0,
            "high_risk":  False,
            "tiers":      []
        }

    # ── Confidence score ───────────────────────────────────────────────────────
    # Multi-factor score — more reliable than raw distance alone
    # Max 100 points total broken into 3 factors:

    if search_mode == "all":
        # Factor 1 — Source diversity (max 40 points)
        # More sources returning results = more confidence
        source_score = 0
        if len(pubmed_papers) > 0:        source_score += 10
        if len(epmc_papers) > 0:          source_score += 10
        if len(trials) > 0:               source_score += 10
        if fda_labels or fda_adverse:     source_score += 10
    else:
        # In uploaded mode we give full source score
        # since the user is intentionally searching their own document
        source_score = 30

    # Factor 2 — Chunk coverage (max 30 points)
    # More relevant chunks = better coverage of the topic
    chunk_score = min(30, len(chunks) * 5)

    # Factor 3 — Distance score (max 30 points)
    # How close is the best matching chunk to the query
    # PubMedBERT distance range: ~150 (perfect) to ~350 (poor)
    best_distance  = min(c["distance"] for c in chunks)
    distance_score = max(0, round((1 - (best_distance - 150) / 200) * 30))

    confidence = min(100, source_score + chunk_score + distance_score)

    # ── Build context for LLM ──────────────────────────────────────────────────
    # Each chunk is formatted with its source metadata
    # so the LLM can cite it properly in the answer
    context = "\n\n---\n\n".join(
        f"[Source: {c['meta'].get('source', 'Unknown')} | "
        f"Year: {c['meta'].get('year', 'N/A')} | "
        f"Link: {c['meta'].get('doi', 'N/A')}]\n\n{c['text']}"
        for c in chunks
    )

    # ── Call Groq LLaMA 3.3 70B ───────────────────────────────────────────────
    # Temperature 0.1 = very deterministic, factual, low creativity
    # This is intentional — we want the model to stick to the context
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"[CONTEXT]\n{context}\n\n[QUESTION]\n{user_query}"}
        ],
        temperature=0.1,
        max_tokens=1024
    )

    answer = response.choices[0].message.content

    # ── Build sources list ─────────────────────────────────────────────────────
    # Deduplicate by DOI and attach tier labels
    sources = []
    seen    = set()
    for c in chunks:
        doi    = c["meta"].get("doi", "")
        source = c["meta"].get("source", "Unknown")
        year   = c["meta"].get("year", "")
        if doi and doi not in seen:
            seen.add(doi)
            sources.append({
                "doi":   doi,
                "label": source,
                "year":  year,
                "tier":  get_tier_label(source)
            })

    return {
        "answer":     answer,
        "sources":    sources,
        "confidence": confidence,
        "high_risk":  is_high_risk(user_query),
        "tiers":      list({s["tier"] for s in sources})
    }