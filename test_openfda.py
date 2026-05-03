from agent.openfda_search import search_openfda_label, search_openfda_adverse, is_drug_query

print("=== Is drug query? ===")
print(is_drug_query("what are the side effects of metformin"))  # should be True
print(is_drug_query("what causes diabetes"))                    # should be False

print("\n=== FDA Label ===")
labels = search_openfda_label("metformin")
for l in labels:
    print(f"Title: {l['title']}")
    print(f"Text (first 300 chars): {l['text'][:300]}")
    print("---")

print("\n=== FDA Adverse Events ===")
adverse = search_openfda_adverse("metformin")
for a in adverse:
    print(a['text'])