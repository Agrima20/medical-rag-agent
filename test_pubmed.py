from agent.pubmed_search import search_pubmed

results = search_pubmed("metformin side effects", max_results=3)

if results:
    for r in results:
        print(f"Title: {r['title']}")
        print(f"Journal: {r['journal']}")
        print(f"PMID: {r['pmid']}")
        print("---")
else:
    print("No results returned from PubMed")