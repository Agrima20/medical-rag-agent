# This file handles live searching of PubMed using the free NCBI E-utilities API
# Workflow: ESearch (get PMIDs) → EFetch (get full abstracts)

import requests
import os
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base URL for all NCBI E-utilities API calls
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# NCBI API key — gives 10 requests/sec
KEY = os.getenv("NCBI_API_KEY")

def search_pubmed(query: str, max_results: int = 5) -> list:
    """
    Search PubMed for a query and return a list of papers with abstracts.
    
    Args:
        query: The medical/research question to search for
        max_results: How many papers to fetch (default 5)
    
    Returns:
        List of dicts, each containing title, abstract, journal, year, doi(digital object identifier)
    """

    # Step 1 — ESearch: search PubMed and get a list of matching PMIDs
    # PMIDs are unique IDs for each paper in PubMed
    search_resp = requests.get(BASE + "esearch.fcgi", params={
        "db": "pubmed",          # search in PubMed database
        "term": query,           # the search query
        "retmax": max_results,   # max number of results to return
        "retmode": "json",       # return response as JSON
        "api_key": KEY           # NCBI API key
    })

    # Extract the list of PMIDs from the JSON response
    pmids = search_resp.json()["esearchresult"]["idlist"]

    # If no papers found, return empty list
    if not pmids:
        return []

    # Step 2 — EFetch: use the PMIDs to fetch full abstracts
    fetch_resp = requests.get(BASE + "efetch.fcgi", params={
        "db": "pubmed",
        "id": ",".join(pmids),   # pass all PMIDs as comma-separated string
        "retmode": "xml",        # abstracts come back in XML format
        "rettype": "abstract",   # we want the abstract type
        "api_key": KEY
    })

    # Step 3 — Parse the XML response into clean Python dicts
    root = ET.fromstring(fetch_resp.text)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        # Extract each field from the XML tree
        pmid     = article.findtext(".//PMID", "")
        title    = article.findtext(".//ArticleTitle", "")
        journal  = article.findtext(".//Journal/Title", "")
        year     = article.findtext(".//PubDate/Year", "")

        # Abstract can have multiple sections (background, methods, results etc.)
        # Join them all into one string
        abstract_parts = article.findall(".//AbstractText")
        abstract = " ".join(p.text or "" for p in abstract_parts)

        papers.append({
            "pmid":     pmid,
            "title":    title,
            "abstract": abstract,
            "journal":  journal,
            "year":     year,
            "doi":      f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"  # direct link to paper
        })

    return papers