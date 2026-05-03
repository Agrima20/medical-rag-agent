# This file handles uploading and parsing of PDF research papers
# It extracts text from PDFs and splits them into small chunks
# Small chunks are better for vector search — more precise retrieval

import fitz  # PyMuPDF — best free library for extracting text from PDFs
from langchain_text_splitters import RecursiveCharacterTextSplitter

def parse_pdf(path: str) -> list:
    """
    Parse a PDF file and split it into overlapping text chunks.
    
    Args:
        path: File path to the PDF
    
    Returns:
        List of dicts, each containing a text chunk and its metadata
    """

    # Open the PDF file
    doc = fitz.open(path)

    # Extract text from every page and join into one big string
    full_text = "\n".join(page.get_text() for page in doc)
    doc.close()

    # Split the full text into smaller overlapping chunks
    # chunk_size=800 chars ≈ ~150-200 words — good size for medical abstracts
    # chunk_overlap=100 chars — overlap between chunks so context isn't lost at boundaries
    # separators — tries to split at paragraph breaks first, then newlines, then sentences
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". "]
    )
    chunks = splitter.split_text(full_text)

    # Get just the filename from the full path (e.g. "study.pdf")
    filename = path.split("\\")[-1]

    # Return each chunk as a dict with metadata
    # Metadata is stored in ChromaDB alongside the text for citation purposes
    return [
        {
            "text":        chunk,
            "source":      filename,        # which file this came from
            "doi":         f"Uploaded PDF: {filename}",  # shown as citation
            "chunk_index": i                # position of chunk in the document
        }
        for i, chunk in enumerate(chunks)
    ]