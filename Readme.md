# 🔬 Medical Research Agent

An AI-powered medical literature assistant that answers clinical and research questions using **only verified, cited sources** — no hallucination, no guesswork.

## The Problem

Doctors and researchers waste hours reading papers. Existing AI tools like ChatGPT hallucinate medical facts, making them dangerous in clinical settings.

## The Solution

A RAG (Retrieval-Augmented Generation) pipeline that:

- Searches verified medical databases in real time
- Retrieves only relevant evidence
- Forces the LLM to answer **strictly from retrieved context**
- Cites every single claim with source, journal, and year

## Sources

| Source             | Type                                  | Coverage     |
| ------------------ | ------------------------------------- | ------------ |
| PubMed             | Peer reviewed abstracts               | 36M+ papers  |
| Europe PMC         | Full text open access                 | 9M+ papers   |
| OpenFDA            | Official drug labels + adverse events | FDA database |
| ClinicalTrials.gov | Completed clinical trials             | NIH registry |
| Uploaded PDFs      | Your own research papers              | Custom       |

## Evidence Tiers

- **Tier 1** — Official FDA regulatory documents
- **Tier 2** — Clinical trials (NIH registered)
- **Tier 3** — Peer reviewed research
- **Tier 4** — Uploaded documents

## Features

- 🔍 Multi-source live search across 4 verified databases
- 📄 Upload your own PDF research papers
- 🎯 Search all sources or uploaded papers only
- ⚠️ Safety warnings for high-risk clinical queries
- 📊 Evidence confidence scoring
- 🔗 Clickable citations with direct links to sources
- 🚫 Zero hallucination — answers only from retrieved context

## Tech Stack

| Layer       | Tool                                           |
| ----------- | ---------------------------------------------- |
| UI          | Streamlit                                      |
| LLM         | Groq (LLaMA 3.3 70B) — free                    |
| Embeddings  | NeuML/pubmedbert-base-embeddings — free, local |
| Vector DB   | ChromaDB — free, local                         |
| PDF parsing | PyMuPDF                                        |

## Setup

1. Clone the repo
2. Create virtual environment

```bash
   python -m venv venv
   venv\Scripts\activate
```

3. Install dependencies

```bash
   pip install -r requirements.txt
```

4. Create `.env` file
5. Run

```bash
   streamlit run app.py
```

## API Keys (all free)

- **Groq** — [console.groq.com](https://console.groq.com)
- **NCBI** — [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account)

## Disclaimer

This tool is for research and educational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment.
