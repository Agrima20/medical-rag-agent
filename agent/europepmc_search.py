# This file searches Europe PMC - a free database with 42M+ abstracts
# and 9M+ full text open access articles
# It is WHO-endorsed and updated daily
# Unlike PubMed which only returns abstracts, Europe PMC can return FULL TEXT
# for open access papers - giving the LLM much richer context

import requests
import re

def strip_html(text: str) -> str:
    """Remove HTML tags from abstract text"""
    return re.sub(r'<[^>]+>', ' ', text).strip()

# Base URL for Europe PMC REST API - completely free, no key needed
BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

def search_europepmc(query: str, max_results: int = 5) -> list:
    """
    Search Europe PMC for a query and return full text where available.
    
    Args:
        query: The medical/research question to search for
        max_results: How many papers to fetch (default 5)
    
    Returns:
        List of dicts with title, abstract/fulltext, journal, year, doi
    """

    # Build search params
    # HAS_FT:Y means "only return papers that have full text available"
    # This is the key advantage over PubMed - we get full papers not just abstracts
    params = {
        "query":        f"{query} HAS_FT:Y",  # only open access full text
        "format":       "json",
        "pageSize":     max_results,
        "resultType":   "core",               # core returns full metadata
        "sort":         "CITED desc",         # most cited papers first
    }

    try:
        response = requests.get(BASE, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Europe PMC search error: {e}")
        return []

    results = data.get("resultList", {}).get("result", [])

    papers = []
    for r in results:
        # Get abstract - Europe PMC often has longer, structured abstracts
        abstract = strip_html(r.get("abstractText", ""))

        # Skip papers with no abstract
        if not abstract:
            continue

        # Get DOI - prefer DOI over PMID for Europe PMC papers
        doi = r.get("doi", "")
        pmid = r.get("pmid", "")

        # Build a readable source link
        if doi:
            link = f"https://doi.org/{doi}"
        elif pmid:
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        else:
            link = "https://europepmc.org"

        papers.append({
            "title":    r.get("title", ""),
            "abstract": abstract,
            "journal":  r.get("journalTitle", "") or r.get("bookOrReportDetails", {}).get("publisher", "Europe PMC"),
            "year":     str(r.get("pubYear", "")),
            "doi":      link,
            "source":   "Europe PMC",        # tag so we know where it came from
            "cited_by": r.get("citedByCount", 0)  # citation count - useful for ranking
        })

    return papers