from agent.europepmc_search import search_europepmc

results = search_europepmc("metformin side effects", max_results=3)

if results:
    for r in results:
        print(f"Title: {r['title']}")
        print(f"Journal: {r['journal']}")
        print(f"Year: {r['year']}")
        print(f"Cited by: {r['cited_by']}")
        print(f"Abstract (first 200 chars): {r['abstract'][:200]}")
        print("---")
else:
    print("No results returned")