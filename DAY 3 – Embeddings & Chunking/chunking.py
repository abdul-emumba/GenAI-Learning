import re
import pandas as pd
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma



PDF_PATH = "pdfs/paper.pdf"
QUESTIONS_PATH = "data/questions.json"

TOP_K = 5

EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

semantic_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

import json

with open(QUESTIONS_PATH) as f:
    QUESTIONS = json.load(f)

def load_pdf():

    loader = PyPDFLoader(PDF_PATH)
    documents = loader.load()

    return documents

def fixed_chunking(documents):
    splitter = CharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=0
    )

    return splitter.split_documents(documents)


def overlapping_chunking(documents):
    splitter = CharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=50
    )

    return splitter.split_documents(documents)


def recursive_chunking(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", "!", "?"]
    )

    return splitter.split_documents(documents)


def sentence_chunking(documents):
    text_splitter = CharacterTextSplitter(
        separator=".",
        chunk_size=200,
        chunk_overlap=0
    )

    return text_splitter.split_documents(documents)


CHUNKING_STRATEGIES = {
    "Fixed": fixed_chunking,
    "Overlap": overlapping_chunking,
    "Recursive": recursive_chunking,
    "Sentence": sentence_chunking,
}

def build_vectorstore(chunks):
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )
    db = Chroma.from_documents(
        chunks,
        embeddings
    )

    return db

def normalize(text):
    return re.sub(r"\s+", " ", text.lower())

def is_hit(retrieved_docs, ground_truth, threshold=0.75):
    """
    Returns True if any retrieved document is semantically similar
    to the ground truth above the threshold.
    """
    gt_emb = semantic_embeddings.embed_query(ground_truth)
    for doc in retrieved_docs:
        doc_emb = semantic_embeddings.embed_query(doc.page_content)
        sim = cosine_similarity(
            np.array(gt_emb).reshape(1, -1),
            np.array(doc_emb).reshape(1, -1)
        )[0][0]

        if sim >= threshold:
            return True

    return False

def evaluate_strategy(strategy_name, chunk_func):
    print(f"\nEvaluating: {strategy_name}")
    documents = load_pdf()
    chunks = chunk_func(documents)
    print("Chunks created:", len(chunks))
    db = build_vectorstore(chunks)

    retriever = db.as_retriever(
        search_kwargs={"k": TOP_K}
    )

    results = []
    hits = 0

    for q in QUESTIONS:
        question = q["question"]
        ground_truth = q["ground_truth"]

        retrieved_docs = retriever._get_relevant_documents(
            question, run_manager=None
        )
        hit = is_hit(retrieved_docs, ground_truth)

        if hit:
            hits += 1

        results.append({
            "question_id": q["id"],
            "hit": hit
        })

    hit_rate = hits / len(QUESTIONS)
    print("Hit Rate:", round(hit_rate, 3))

    return results, hit_rate

def run_evaluation():

    strategy_results = {}
    hit_rates = {}

    for name, func in CHUNKING_STRATEGIES.items():
        results, hit_rate = evaluate_strategy(name,func)
        strategy_results[name] = results
        hit_rates[name] = hit_rate

    return strategy_results, hit_rates

def build_comparison_table(strategy_results):

    table = []
    question_ids = [
        q["id"] for q in QUESTIONS
    ]

    for qid in question_ids:
        row = {
            "Question": qid
        }

        for strategy in strategy_results:
            hit = next(
                r["hit"]
                for r in strategy_results[strategy]
                if r["question_id"] == qid
            )

            row[strategy] = "✓" if hit else "✗"

        table.append(row)

    df = pd.DataFrame(table)

    return df

def analyze_improvements(strategy_results):
    improved_cases = []
    worse_cases = []

    for q in QUESTIONS:
        qid = q["id"]
        fixed_hit = next(
            r["hit"]
            for r in strategy_results["Fixed"]
            if r["question_id"] == qid
        )

        recursive_hit = next(
            r["hit"]
            for r in strategy_results["Recursive"]
            if r["question_id"] == qid
        )

        if not fixed_hit and recursive_hit:
            improved_cases.append(qid)

        if fixed_hit and not recursive_hit:
            worse_cases.append(qid)

    return improved_cases[:5], worse_cases[:3]


if __name__ == "__main__":
    strategy_results, hit_rates = run_evaluation()
    print("\nHit Rate@5 Comparison")
    for strategy, rate in hit_rates.items():
        print(strategy,":",round(rate, 3))

    df = build_comparison_table(
        strategy_results
    )
    print("\nPer Question Comparison")
    print(df)

    improved, worse = analyze_improvements(
        strategy_results
    )
    print("\n5 Cases Where Advanced Chunking Improved")
    print(improved)
    print("\n3 Cases Where Advanced Chunking Performed Worse")
    print(worse)