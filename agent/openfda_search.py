# This file searches OpenFDA - the official FDA database
# It is completely free, no API key needed for basic use
# Best used when the query is about a specific drug - labels, side effects,
# recalls, adverse events
# Source: https://open.fda.gov

import requests

# Base URL for OpenFDA API
BASE = "https://api.fda.gov/drug/"

def is_drug_query(query: str) -> bool:
    """
    Detect if the user query is asking about a specific drug.
    If yes, we search OpenFDA in addition to PubMed/EuropePMC.
    
    Simple keyword detection - can be improved later with NLP.
    """
    drug_keywords = [
        "drug", "medication", "medicine", "dose", "dosage",
        "side effect", "adverse", "interaction", "contraindication",
        "overdose", "prescription", "tablet", "capsule", "injection",
        "recall", "warning", "label", "mg", "treatment with"
    ]
    query_lower = query.lower()
    return any(kw in query_lower for kw in drug_keywords)


def search_openfda_label(drug_name: str) -> list:
    """
    Search FDA drug labels for a specific drug.
    Returns official prescribing information including:
    - Indications and usage
    - Warnings and precautions
    - Adverse reactions
    - Drug interactions
    - Dosage and administration
    
    Args:
        drug_name: Name of the drug to search for
    
    Returns:
        List of dicts with official FDA label information
    """
    try:
        response = requests.get(
            BASE + "label.json",
            params={
                "search": f"openfda.generic_name:\"{drug_name}\"",
                "limit": 3   # top 3 label matches
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"OpenFDA label search error: {e}")
        return []

    results = []
    for r in data.get("results", []):
        # Extract the most clinically useful sections from the FDA label
        # These are official FDA-approved descriptions

        indications    = " ".join(r.get("indications_and_usage", []))
        warnings       = " ".join(r.get("warnings", []))
        adverse        = " ".join(r.get("adverse_reactions", []))
        interactions   = " ".join(r.get("drug_interactions", []))
        dosage         = " ".join(r.get("dosage_and_administration", []))
        contraindicate = " ".join(r.get("contraindications", []))

        # Only include sections that have content
        sections = []
        if indications:
            sections.append(f"INDICATIONS: {indications[:500]}")
        if warnings:
            sections.append(f"WARNINGS: {warnings[:500]}")
        if adverse:
            sections.append(f"ADVERSE REACTIONS: {adverse[:500]}")
        if interactions:
            sections.append(f"DRUG INTERACTIONS: {interactions[:500]}")
        if dosage:
            sections.append(f"DOSAGE: {dosage[:500]}")
        if contraindicate:
            sections.append(f"CONTRAINDICATIONS: {contraindicate[:500]}")

        if not sections:
            continue

        # Get drug name from FDA metadata
        brand_names   = r.get("openfda", {}).get("brand_name", ["Unknown"])
        generic_names = r.get("openfda", {}).get("generic_name", ["Unknown"])

        results.append({
            "text":    "\n\n".join(sections),
            "source":  "FDA Official Drug Label",
            "journal": "U.S. Food and Drug Administration (FDA)",
            "doi":     "https://open.fda.gov/drug/label/",
            "year":    "Current",                          # FDA labels are living documents
            "title":   f"FDA Label: {brand_names[0]} ({generic_names[0]})",
            "tier":    1   # tier 1 = official regulatory document = highest trust
        })

    return results


def search_openfda_adverse(drug_name: str) -> list:
    """
    Search FDA Adverse Event Reporting System (FAERS) for a drug.
    Returns real-world reports of side effects submitted by doctors,
    patients and manufacturers to the FDA.
    
    Args:
        drug_name: Name of the drug to search for
    
    Returns:
        List of dicts summarizing the most common adverse events
    """
    try:
        response = requests.get(
            BASE + "event.json",
            params={
                # Count the most common reactions reported for this drug
                "search": f"patient.drug.medicinalproduct:\"{drug_name}\"",
                "count":  "patient.reaction.reactionmeddrapt.exact",
                "limit":  10   # top 10 most reported reactions
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"OpenFDA adverse event search error: {e}")
        return []

    results = data.get("results", [])
    if not results:
        return []

    # Format the top adverse events into a readable summary
    reactions = [
        f"{r['term']} ({r['count']} reports)"
        for r in results[:10]
    ]

    summary = (
        f"Most commonly reported adverse events for {drug_name} "
        f"in the FDA Adverse Event Reporting System (FAERS):\n"
        + "\n".join(f"- {rx}" for rx in reactions)
    )

    return [{
        "text":    summary,
        "source":  "FDA Adverse Event Reporting System (FAERS)",
        "journal": "U.S. Food and Drug Administration (FDA)",
        "doi":     "https://open.fda.gov/drug/event/",
        "year":    "Current",
        "title":   f"FDA FAERS Report: {drug_name}",
        "tier":    1   # official FDA data = tier 1
    }]