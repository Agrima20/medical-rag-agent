# Main Streamlit UI
# Now shows: answer, sources with tier labels, confidence score, safety warnings

import streamlit as st
import os
from agent.pdf_ingestor import parse_pdf
from agent.vectorstore import add_documents
from agent.rag_pipeline import answer_query

st.set_page_config(
    page_title="Medical Research Agent",
    layout="wide"
)

st.title("🩺 Medical Research Agent")
st.caption(
    "Every answer backed by real research. Every claim has a source."
)
st.divider()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Upload Research Papers")
    st.caption("Upload your own PDFs to include them alongside live sources or search them separately")

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type="pdf",
        accept_multiple_files=True
    )

    if uploaded_files:
        os.makedirs("data/uploads", exist_ok=True)
        for f in uploaded_files:
            save_path = f"data/uploads/{f.name}"
            with open(save_path, "wb") as out:
                out.write(f.read())
            with st.spinner(f"Indexing {f.name}..."):
                from agent.pdf_ingestor import parse_pdf
                chunks = parse_pdf(save_path)
                add_documents(chunks)
            st.success(f"✅ Indexed {f.name} ({len(chunks)} chunks)")

    st.divider()
    st.markdown("**Sources searched automatically:**")
    st.markdown("- PubMed (36M+ papers)")
    st.markdown("- Europe PMC (9M+ full text)")
    st.markdown("- OpenFDA (drug labels + adverse events)")
    st.markdown("- ClinicalTrials.gov (completed trials)")
    st.markdown("- Your uploaded PDFs")
    st.divider()
    st.markdown("**Evidence tiers:**")
    st.markdown("- Tier 1 — FDA / Regulatory")
    st.markdown("- Tier 2 — Clinical Trials (NIH)")
    st.markdown("- Tier 3 — Peer Reviewed Research")

# ── Main query area ────────────────────────────────────────────────────────────
query = st.text_input(
    "Ask a clinical or research question",
    placeholder="e.g. What are the side effects of metformin in elderly patients?"
)

# Search mode toggle
search_mode = st.radio(
    "Search mode",
    options=["all", "uploaded"],
    format_func=lambda x: "🌐 Search all sources (PubMed + FDA + ClinicalTrials + uploaded PDFs)" 
                          if x == "all" 
                          else "📄 Search uploaded papers only",
    horizontal=True
)

if st.button("🔍 Search Literature", type="primary") and query:

    if search_mode == "uploaded":
        spinner_text = "Searching your uploaded papers..."
    else:
        spinner_text = "Searching PubMed, Europe PMC, FDA, ClinicalTrials.gov..."

    with st.spinner(spinner_text):
        result = answer_query(query, search_mode=search_mode)

    # ── Confidence score ───────────────────────────────────────────────────────
    conf = result["confidence"]
    if conf >= 70:
        conf_color = "green"
        conf_label = "High confidence"
    elif conf >= 40:
        conf_color = "orange"
        conf_label = "Moderate confidence"
    else:
        conf_color = "red"
        conf_label = "Low confidence — verify manually"

    st.markdown(
        f"**Evidence confidence:** :{conf_color}[{conf_label} ({conf}%)]"
    )

    # ── High risk warning ──────────────────────────────────────────────────────
    if result["high_risk"]:
        st.warning(
            "⚠️ This query involves clinical decision-making (dosage, diagnosis, or treatment). "
            "The information below is for research reference only. "
            "Always consult a licensed medical professional."
        )

    # ── Answer ─────────────────────────────────────────────────────────────────
    st.markdown("### Answer")
    st.markdown(result["answer"])

    # ── Sources with tier labels ───────────────────────────────────────────────
    if result["sources"]:
        st.markdown("### Sources:")
        for src in result["sources"]:
            tier  = src.get("tier", "")
            label = src.get("label", "")
            year  = src.get("year", "")
            doi   = src.get("doi", "")

            if doi.startswith("http"):
                st.markdown(f"- {tier} | **{label}** ({year}) → [View Source]({doi})")
            else:
                st.markdown(f"- {tier} | **{label}** ({year})")

    # ── Disclaimer ─────────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "⚠️ This tool is for research and educational purposes only. "
        "It is not a substitute for professional medical advice, diagnosis, or treatment. "
        "All answers are sourced from publicly available verified medical databases."
    )