import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

from rag_pipeline import RagPipeline

# Initialize Embeddings & RAG
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
pipeline = RagPipeline(embeddings=embeddings)

st.title("Preference-Aware Travel RAG")

# Query input
query = st.text_input("Enter your travel query:", "")

# Optional: list of URLs to ingest
urls_input = st.text_area(
    "Enter URLs to ingest (one per line, optional if already ingested):", ""
)
urls = [u.strip() for u in urls_input.split("\n") if u.strip()]

if st.button("Ingest URLs"):
    if urls:
        with st.spinner("Fetching, chunking, and storing content..."):
            pipeline.ingest_urls(urls)
        st.success("Ingestion complete!")
    else:
        st.warning("Please provide at least one URL to ingest.")

if st.button("Search"):
    if not query:
        st.warning("Enter a query first!")
    else:
        with st.spinner("Retrieving relevant content..."):
            results = pipeline.query(query, top_k=8)
        
        st.subheader("Query Analysis")
        st.write(f"**Extracted Preferences:** {results['preferences']}")
        st.write(f"**Applied Filters:** {results['filters']}")
        st.write(f"**Retrieval Judgment:** {results['judgment']}")
        st.write(f"**Number of Documents Retrieved:** {results['retrieved_docs']}")
        st.subheader("Final Answer")
        st.write(results['final_answer'])