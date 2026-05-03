from agent.clinicaltrials_search import search_clinicaltrials

results = search_clinicaltrials("metformin type 2 diabetes", max_results=3)

if results:
    for r in results:
        print(f"Title: {r['title']}")
        print(f"Source: {r['doi']}")
        print(f"Text (first 300 chars): {r['text'][:300]}")
        print("---")
else:
    print("No results returned")