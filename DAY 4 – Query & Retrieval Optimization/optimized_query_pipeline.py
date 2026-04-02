import json
import os
import re
from anyio import sleep
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from langchain_community.llms import HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate
from sentence_transformers import SentenceTransformer, util
from langchain_community.retrievers import BM25Retriever

from transformers import pipeline
from sentence_transformers import CrossEncoder

from groq import Groq


TEMPERATURE = 0
MAX_TOKENS = 1024
GOLDEN_DATASET_PATH = "data/questions.json"
OUTPUT_RESULTS = "rag_results.json"

model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
client = Groq()
print("Groq client initialized successfully.")

SECTION_RANGES = [
    (1, 1, "Abstract"),
    (2, 2, "1 Introduction"),
    (3, 3, "2 Related Work"),
    (3, 3, "3 Tasks and Datasets"),
    (3, 4, "3.1 NeedleBench Information-Sparse Tasks"),
    (5, 5, "3.2 NeedleBench Information-Dense Tasks"),
    (6, 6, "4 Experiments"),
    (6, 6, "4.1 Performance of NeedleBench Information-Sparse Tasks"),
    (6, 6, "4.1.1 Impact of Model Architecture and Technical Advances on Retrieval Performance"),
    (7, 7, "4.1.2 Challenges in Multi-Needle Reasoning Compared to Retrieval Tasks"),
    (8, 8, "4.1.3 Effect of Model Scale on Multi-Needle Reasoning Performance"),
    (9, 9, "4.1.4 Effect of Needle Count on Multi-Needle Reasoning Performance"),
    (9, 10, "4.1.5 Impact of Language: Which Model Performs Better under the Bilingual Scenario?"),
    (11, 12, "4.2 NeedleBench Information-Dense Task"),
    (13, 13, "5 Conclusion and Future Work"),
    (13, 16, "References"),
    (17, 17, "A Evaluated Models"),
    (17, 17, "B Performance of Long CoT Model on Information-Sparse Tasks at NeedleBench 128K"),
    (17, 18, "C Detailed Multi-Needle Reasoning Performance at 32K and 128K"),
    (19, 19, "D Realistic vs Synthetic Multi-Needle Reasoning Tasks"),
    (20, 20, "E ATC Data Generation Algorithm"),
    (20, 20, "F Output Format Compliance Analysis"),
    (21, 22, "G NeedleBench Prompt Examples"),
    (23, 31, "H Error Analysis Examples"),
]

def get_sections_from_page(page_num: int):
    sections = [section for start, end, section in SECTION_RANGES if start <= page_num <= end]
    return sections if sections else ["Unknown"]

def load_dataset(path):
    with open(path, 'r') as f:
        dataset = json.load(f)
    return dataset

class PDFLoader:
    def __init__(self, file_paths):
        self.file_paths = file_paths

    def load(self):
        documents = []
        for path in self.file_paths:
            loader = PyPDFLoader(path)
            docs = loader.load()
            for doc in docs:
                page_num = int(doc.metadata.get("page_label", 0))

                sections = get_sections_from_page(page_num)

                doc.metadata.update({
                    "source": path,
                    "page": page_num,
                    "section": sections,
                    "section_str": " > ".join(sections),
                    "date": "2026-03-31"
                })
            documents.extend(docs)
        return documents


class TextProcessor:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,          # larger chunks = more context
            chunk_overlap=120,       # preserve continuity
            separators=[
                "\n\n###",           # headings first
                "\n\n",
                "\n",
                ". ",
                " "
            ]
        )

    def split(self, documents):
        return self.splitter.split_documents(documents)


class VectorStoreManager:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings()

    def create_store(self, documents):
        vectordb = Chroma.from_documents(documents, self.embedding_model)

        bm25 = BM25Retriever.from_documents(documents)
        bm25.k = 5

        return vectordb, bm25


class QAEngine:
    def __init__(self, vectordb, model_name="llama-3.1-8b-instant"):
        self.retriever = vectordb.as_retriever(search_kwargs={"k": 5})
        self.model_name = model_name

        # Prompt template
        self.prompt_template = """Answer the question based only on the context below.
                                Context:
                                {context}
                                Question:
                                {question}"""

    def ask(self, query, answer_type=None):
        # Retrieve relevant documents (version-compatible)
        docs = self.retriever._get_relevant_documents(query, run_manager=None)

        # Join text from chunks
        context_text = "\n\n".join([doc.page_content for doc in docs])

        # Format prompt
        final_prompt = self.prompt_template.format(
            context=context_text,
            question=query
        )

        # Use Groq model instead of HuggingFace
        answer = run_model(
            model_name=self.model_name,
            prompt=final_prompt,
            answer_type=answer_type
        )

        return answer



class RAGPipeline:
    def __init__(self, pdf_paths, model_name="llama-3.1-8b-instant"):
        self.pdf_paths = pdf_paths
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.qa_engine = None
        self.model_name = model_name
        self.vectordb = None
        self.bm25 = None

    def build(self):
        print("Loading PDFs...")
        loader = PDFLoader(self.pdf_paths)
        documents = loader.load()
        print(f"Loaded {len(documents)} pages")

        print("Splitting documents...")
        processor = TextProcessor()
        chunks = processor.split(documents)
        print(f"Created {len(chunks)} chunks")

        print("Creating vector store...")
        vector_manager = VectorStoreManager()
        self.vectordb, self.bm25 = vector_manager.create_store(chunks)

        print("Initializing QA engine...")
        self.qa_engine = QAEngine(self.vectordb)

        print("RAG Pipeline Ready!")

    def query(self, question, answer_type):
        if not self.qa_engine:
            raise Exception("Pipeline not built. Call build() first.")
        return self.qa_engine.ask(question, answer_type)
    
    def hyde_query(self, question, k=5, metadata_filter=None):
        """
        HyDE: Generate a hypothetical answer, then retrieve using its embedding.
        """
        # Step 1: Generate hypothetical answer
        hyde_answer = run_model(
            model_name=self.model_name,
            prompt=question,
            answer_type="hyde"
        )
        print("Hypothetical Answer:", hyde_answer)

        # Step 2: Convert hypothetical answer to embedding
        embedding_model = HuggingFaceEmbeddings()
        hyde_embedding = embedding_model.embed_query(hyde_answer)

        # Step 3: Retrieve top-k documents using embedding
        docs = self.vectordb.similarity_search_by_vector(hyde_embedding, k=k)

        # Step 4: Combine chunks into context
        context_text = "\n\n".join([doc.page_content for doc in docs])

        # Step 5: Ask final QA model using retrieved context
        final_prompt = f"""
            Answer the question based only on the context below.
            Context:
            {context_text}
            Question:
            {question}
            """
        answer = run_model(
            model_name=self.model_name,
            prompt=final_prompt,
            answer_type=None
        )
        return answer
    
    def generate_multi_queries(self, question, n=3):
        """
        Generate multiple query variations using LLM.
        """

        prompt = f"""
        Generate {n} different search queries that mean the same thing.

        Original question:
        {question}

        Return each query on a new line.
        """

        response = run_model(
            model_name=self.model_name,
            prompt=prompt,
            answer_type=None
        )

        queries = [
            q.strip("- ").strip()
            for q in response.split("\n")
            if q.strip()
        ]

        # remove first index containing: Here are three different search queries that mean the same thing:
        queries = queries[1:]

        # append original question to the list of queries
        queries.append(question)
        print(f"\nGenerated Multi Queries: {queries}\n")

        return queries
    
    def rerank_documents(self, question, documents, top_k=5):
        if not documents:
            return []

        pairs = [(question, doc.page_content) for doc in documents]

        scores = self.reranker.predict(pairs)

        scored_docs = list(zip(documents, scores))

        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in scored_docs[:top_k]]   # IMPORTANT: cut to top_k

    def multi_query(self, question, k=3, metadata_filter=None):
        """
        Multi-query retrieval.
        """

        embedding_model = HuggingFaceEmbeddings()
        # Step 1 — generate multiple queries
        queries = self.generate_multi_queries(question)

        all_docs = []
        # Step 2 — retrieve docs for each query
        for q in queries:
            embedding = embedding_model.embed_query(q)
            docs = self.vectordb.similarity_search_by_vector(
                embedding,
                k=k,
            )

            all_docs.extend(docs)

        # Step 3 — remove duplicates
        unique_docs = {}
        for doc in all_docs:
            key = doc.page_content
            unique_docs[key] = doc

        final_docs = list(unique_docs.values())

        print("Total retrieved docs:", len(final_docs))
        # Step 4 — build context
        context_text = "\n\n".join(
            doc.page_content for doc in final_docs
        )

        # Step 5 — final answer generation
        final_prompt = f"""
        Answer the question based only on the context below.

        Context:
        {context_text}

        Question:
        {question}
        """

        answer = run_model(
            model_name=self.model_name,
            prompt=final_prompt,
            answer_type=None
        )

        return answer
    
    def multi_query_hybrid_retrieval(self, question, k=5, metadata_filter=None, rerank=False):
        """
        Multi-query + Hybrid Retrieval + Optional Reranking

        Hybrid = Vector search + Keyword search
        Rerank controlled by flag.
        """

        embedding_model = HuggingFaceEmbeddings()

        print("\nRunning Multi-Query Hybrid Retrieval")

        # Step 1 — generate multiple queries
        queries = self.generate_multi_queries(question)

        all_docs = []



        # Step 2 — HYBRID RETRIEVAL
        for q in queries:

            print("\nQuery:", q)

            embedding = embedding_model.embed_query(q)
            vector_docs = self.vectordb.similarity_search_by_vector(
                embedding,
                k=k
            )

            print("Vector docs:", len(vector_docs))

            keyword_docs = self.bm25._get_relevant_documents(q, run_manager=None)
        
            print("Keyword docs:", len(keyword_docs))

            all_docs.extend(vector_docs)
            all_docs.extend(keyword_docs)

        # Step 3 — remove duplicates
        unique_docs = {}

        for doc in all_docs:
            key = key = (doc.metadata.get("page"), doc.page_content[:100])
            unique_docs[key] = doc

        final_docs = list(unique_docs.values())

        print("Total retrieved docs:", len(final_docs))

        # Step 4 — OPTIONAL RERANKING
        if rerank:
            print("Reranking enabled")
            final_docs = self.rerank_documents(
                question,
                final_docs,
                top_k=k
            )

            print("Docs after reranking:", len(final_docs))

        # Step 5 — build context
        context_text = "\n\n".join(
            "Content: " + doc.page_content + "\n\n" + "Metadata: " + str(doc.metadata) for doc in final_docs
        )

        # Step 6 — final answer generation
        final_prompt = f"""
        Answer the question based only on the context below.

        Context:
        {context_text}

        Question:
        {question}
        """

        answer = run_model(
            model_name=self.model_name,
            prompt=final_prompt,
            answer_type='json_hybrid_retrieval'
        )

        return answer
    
def run_model(model_name, prompt, answer_type=None, system_prompt='You are a helpful assistant.'):
    if answer_type == 'factual':
        dev_inst = "Answer factually based on the context."
    elif answer_type == 'reasoning':
        dev_inst = "Provide a reasoned explanation based on the context."
    elif answer_type == 'negative':
        dev_inst = "If the information is not mentioned in the context, state 'Not mentioned in the document.' Otherwise, answer based on the context."
    elif answer_type == 'hyde':
        dev_inst = "Generate a short hypothetical answer to the question without looking at any context."
    elif answer_type == 'hybrid_retrieval':
        dev_inst = "Add citations in the format [source, section, page #] for any information you use from the context."
    elif answer_type == 'json_hybrid_retrieval':
        dev_inst = """
        Output your response strictly in JSON format with these fields:
                {
                "answer": "<your answer with referenced facts>",
                "citations": ["<source 1>", "<source 2>", ...],
                "confidence": "<high / medium / low>"
                }

                Rules:
                1. Do not include information without a source.
                2. Each citation should clearly support the corresponding part of your answer.
                3. Confidence is based on the reliability of sources and the specificity of the answer.
        """
    else:
        dev_inst = "Always answer based on the context."

    full_prompt = f"""
        System: {system_prompt}
        Developer Instruction: {dev_inst}
        User Prompt: {prompt}
        """

    response = client.chat.completions.create(
        model=model_name,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        messages=[{'role':'user','content':full_prompt}]
    )
    return response.choices[0].message.content

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s%-]', '', text)
    return text.strip()


def extract_keywords(ground_truth: str):
    """
    Extract:
    - numbers (10, 50%)
    - uppercase terms (ATC, ENL)
    - longer meaningful words
    """
    numbers = re.findall(r'\b\d+%?\b', ground_truth)
    caps = re.findall(r'\b[A-Z]{2,}\b', ground_truth)

    long_words = [
        w.lower() for w in ground_truth.split()
        if len(w) > 6
    ]

    keywords = set([w.lower() for w in numbers + caps + long_words])
    return list(keywords)


def keyword_score(answer: str, keywords):
    if not keywords:
        return 0.0

    answer = normalize_text(answer)

    matches = sum(1 for kw in keywords if kw in answer)
    ratio = matches / len(keywords)

    if ratio >= 0.6:
        return 1.0      # strong match
    elif ratio >= 0.3:
        return 0.5      # partial match
    else:
        return 0.0


def is_correct_enhanced(
    answer,
    ground_truth,
    semantic_pass=0.70,
    semantic_partial=0.55,
    w_semantic=0.6,
    w_keyword=0.4
):
    if not answer or answer.strip() == "":
        return {
            "status": "FAIL",
            "semantic_score": 0.0,
            "keyword_score": 0.0,
            "final_score": 0.0,
            "failure_type": "RETRIEVAL_FAILURE"
        }

    # --- Semantic similarity ---
    embeddings = model.encode([answer, ground_truth])
    semantic = util.cos_sim(embeddings[0], embeddings[1]).item()

    # --- Keyword matching ---
    keywords = extract_keywords(ground_truth)
    key_score = keyword_score(answer, keywords)

    # --- Final weighted score ---
    final_score = (w_semantic * semantic) + (w_keyword * key_score)

    # --- Status classification ---
    if semantic >= semantic_pass or key_score == 1.0:
        status = "PASS"
    elif semantic >= semantic_partial or key_score > 0:
        status = "PARTIAL"
    else:
        status = "FAIL"

    # --- Failure type (debugging RAG) ---
    if status == "PASS":
        failure_type = "NONE"
    elif key_score == 0 and semantic < 0.5:
        failure_type = "RETRIEVAL_FAILURE"
    elif key_score > 0 and semantic < semantic_pass:
        failure_type = "GENERATION_FAILURE"
    else:
        failure_type = "PARTIAL_UNCERTAIN"

    return {
        "status": status,
        "semantic_score": round(semantic, 3),
        "keyword_score": key_score,
        "final_score": round(final_score, 3),
        "failure_type": failure_type
    }

def is_correct(answer, ground_truth, threshold=0.7):
    if not answer or answer.strip() == "":
        return {"is_correct": False, "similarity": 0.0}

    embeddings = model.encode([answer, ground_truth])

    similarity = util.cos_sim(embeddings[0], embeddings[1]).item()

    is_match = similarity >= threshold

    return {
        "is_correct": is_match,
        "similarity": similarity
    }

def main():
    pdfs = [
        "pdfs/paper.pdf",
    ]

    pipeline = RAGPipeline(pdfs)
    pipeline.build()

    dataset = load_dataset(GOLDEN_DATASET_PATH)
    results = []

    for row in dataset:
        question = row['question']
        ground_truth = row['ground_truth']

        metadata_filter = {
            "section_str": row.get("section"),
        }

        print(f"Question: {question}")

        #answer = pipeline.query(question, answer_type=None)
        #answer_hyde = pipeline.hyde_query(question, metadata_filter=metadata_filter)
        #answer_multi = pipeline.multi_query(question, metadata_filter=metadata_filter)
        #answer_multi_hybrid_unrancked = pipeline.multi_query_hybrid_retrieval(question, metadata_filter=metadata_filter, rerank=False)
        answer_multi_hybrid_ranked = pipeline.multi_query_hybrid_retrieval(question, metadata_filter=metadata_filter, rerank=True)

        #correct = is_correct(answer, ground_truth)
        #correct_hyde = is_correct(answer_hyde, ground_truth)
        #correct_multi = is_correct(answer_multi, ground_truth)
        #correct_multi_hybrid_unranked = is_correct(answer_multi_hybrid_unrancked, ground_truth)
        correct_multi_hybrid_ranked = is_correct(answer_multi_hybrid_ranked, ground_truth)
        #correct_multi_hybrid_ranked_enhanced = is_correct_enhanced(answer_multi_hybrid_ranked, ground_truth)


        result = {
            'question': question,
            'ground_truth': ground_truth,
            'answer_multi_hybrid_ranked': answer_multi_hybrid_ranked,
            #'results': correct_multi_hybrid_ranked_enhanced,
            #'answer': answer,
            #'answer_hyde': answer_hyde,
            #'answer_multi': answer_multi,
            #'answer_multi_hybrid_unranked': answer_multi_hybrid_unrancked,
            #'correct_multi_hybrid_unranked': correct_multi_hybrid_unranked['is_correct'],
            #'similarity_multi_hybrid_unranked': correct_multi_hybrid_unranked['similarity'],
            #'status_multi_hybrid_unranked': 'PASS' if correct_multi_hybrid_unranked['is_correct'] else 'FAIL',
            'answer_multi_hybrid_ranked': answer_multi_hybrid_ranked,
            'correct_multi_hybrid_ranked': correct_multi_hybrid_ranked['is_correct'],
            'similarity_multi_hybrid_ranked': correct_multi_hybrid_ranked['similarity'],
            'status_multi_hybrid_ranked': 'PASS' if correct_multi_hybrid_ranked['is_correct'] else 'FAIL',
            #'correct': correct['is_correct'],
            #'similarity': correct['similarity'],
            #'correct_hyde': correct_hyde['is_correct'],
            #'similarity_hyde': correct_hyde['similarity'],
            #'correct_multi': correct_multi['is_correct'],
            #'similarity_multi': correct_multi['similarity'],
            #'status': 'PASS' if correct['is_correct'] else 'FAIL',
            #'status_hyde': 'PASS' if correct_hyde['is_correct'] else 'FAIL',
            #'status_multi': 'PASS' if correct_multi['is_correct'] else 'FAIL'
        }

        results.append(result)

    # append results to existing json file if it exists, otherwise create new file
    if os.path.exists(OUTPUT_RESULTS):
        with open(OUTPUT_RESULTS, 'r') as f:
            existing_results = json.load(f)
        existing_results.extend(results)
        with open(OUTPUT_RESULTS, 'w') as f:
            json.dump(existing_results, f, indent=2)
    else:
        with open(OUTPUT_RESULTS, 'w') as f:
            json.dump(results, f, indent=2)




if __name__ == "__main__":
    main()