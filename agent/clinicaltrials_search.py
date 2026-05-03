# This file searches ClinicalTrials.gov - the official US registry of
# all clinical trials worldwide. Run by the NIH, completely free.
# Very useful for queries about treatments, ongoing research, drug efficacy
# Every trial here has gone through IRB/ethics approval - highly verified source

import requests

# ClinicalTrials.gov API v2 - updated in 2023, more powerful than v1
BASE = "https://clinicaltrials.gov/api/v2/studies"

def search_clinicaltrials(query: str, max_results: int = 3) -> list:
    """
    Search ClinicalTrials.gov for studies related to a query.
    Focuses on completed trials with results - most useful for evidence.
    
    Args:
        query: The medical/research question
        max_results: How many trials to fetch (default 3)
    
    Returns:
        List of dicts with trial info, results summary, and official link
    """

    params = {
        "query.term":   query,
        "filter.overallStatus": "COMPLETED",  # only completed trials
        "fields": ",".join([                   # only fetch fields we need
            "NCTId",
            "BriefTitle",
            "BriefSummary",
            "Condition",
            "InterventionName",
            "OverallStatus",
            "StartDate",
            "CompletionDate",
            "EnrollmentCount",
            "Phase",
            "PrimaryOutcomeMeasure"
        ]),
        "pageSize": max_results,
        "sort": "LastUpdatePostDate:desc"      # most recently updated first
    }

    try:
        response = requests.get(BASE, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"ClinicalTrials.gov search error: {e}")
        return []

    studies = data.get("studies", [])
    if not studies:
        return []

    results = []
    for study in studies:
        # Navigate the nested JSON structure of ClinicalTrials API v2
        protocol = study.get("protocolSection", {})
        id_module         = protocol.get("identificationModule", {})
        desc_module       = protocol.get("descriptionModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        design_module     = protocol.get("designModule", {})
        interventions     = protocol.get("armsInterventionsModule", {})
        outcomes          = protocol.get("outcomesModule", {})
        status_module     = protocol.get("statusModule", {})

        nct_id    = id_module.get("nctId", "")
        title     = id_module.get("briefTitle", "")
        summary   = desc_module.get("briefSummary", "")
        condition = ", ".join(conditions_module.get("conditions", []))
        phase     = ", ".join(design_module.get("phases", ["N/A"]))
        enrollment = design_module.get("enrollmentInfo", {}).get("count", "N/A")

        # Get intervention names (drugs/treatments being tested)
        intervention_list = interventions.get("interventions", [])
        intervention_names = ", ".join([
            i.get("name", "") for i in intervention_list
        ])

        # Get primary outcome measure
        primary_outcomes = outcomes.get("primaryOutcomes", [])
        primary_outcome = primary_outcomes[0].get("measure", "") if primary_outcomes else ""

        # Completion date
        completion = status_module.get("completionDateStruct", {}).get("date", "N/A")

        if not summary:
            continue

        # Format into a structured text block for the LLM
        text = (
            f"CLINICAL TRIAL: {title}\n"
            f"Condition: {condition}\n"
            f"Phase: {phase}\n"
            f"Enrollment: {enrollment} participants\n"
            f"Interventions: {intervention_names}\n"
            f"Primary Outcome: {primary_outcome}\n"
            f"Completion: {completion}\n\n"
            f"Summary: {summary[:800]}"
        )

        results.append({
            "text":    text,
            "title":   title,
            "source":  "ClinicalTrials.gov",
            "journal": "U.S. National Institutes of Health (NIH)",
            "doi":     f"https://clinicaltrials.gov/study/{nct_id}",
            "year":    completion[:4] if completion != "N/A" else "",
            "tier":    2   # tier 2 = clinical trial = high evidence
        })

    return results