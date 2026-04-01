import json
from anyio import sleep
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from langchain_community.llms import HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate
from sentence_transformers import SentenceTransformer, util

from transformers import pipeline
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
                doc.metadata.update({
                    "source": path,
                    "page": page_num,
                    "section": get_sections_from_page(page_num),
                    "date": "2026-03-31"
                })
            documents.extend(docs)
        return documents


class TextProcessor:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?"]
        )

    def split(self, documents):
        return self.splitter.split_documents(documents)


class VectorStoreManager:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings()

    def create_store(self, documents):
        vectordb = Chroma.from_documents(documents, self.embedding_model)
        return vectordb


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
        self.qa_engine = None
        self.model_name = model_name
        self.vectordb = None

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
        self.vectordb = vector_manager.create_store(chunks)

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

        print(f"\nGenerated Multi Queries: {queries}\n")

        return queries
    
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
    
def run_model(model_name, prompt, answer_type=None, system_prompt='You are a helpful assistant.'):
    if answer_type == 'factual':
        dev_inst = "Answer factually based on the context."
    elif answer_type == 'reasoning':
        dev_inst = "Provide a reasoned explanation based on the context."
    elif answer_type == 'negative':
        dev_inst = "If the information is not mentioned in the context, state 'Not mentioned in the document.' Otherwise, answer based on the context."
    elif answer_type == 'hyde':
        dev_inst = "Generate a short hypothetical answer to the question without looking at any context."
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
            "section": row.get("section"),
        }

        print(f"Question: {question}")

        #answer = pipeline.query(question, answer_type=None)
        #answer_hyde = pipeline.hyde_query(question, metadata_filter=metadata_filter)
        answer_multi = pipeline.multi_query(question, metadata_filter=metadata_filter)

        #correct = is_correct(answer, ground_truth)
        #correct_hyde = is_correct(answer_hyde, ground_truth)
        correct_multi = is_correct(answer_multi, ground_truth)

        result = {
            'question': question,
            'ground_truth': ground_truth,
            #'answer': answer,
            #'answer_hyde': answer_hyde,
            'answer_multi': answer_multi,
            #'correct': correct['is_correct'],
            #'similarity': correct['similarity'],
            #'correct_hyde': correct_hyde['is_correct'],
            #'similarity_hyde': correct_hyde['similarity'],
            'correct_multi': correct_multi['is_correct'],
            'similarity_multi': correct_multi['similarity'],
            #'status': 'PASS' if correct['is_correct'] else 'FAIL',
            #'status_hyde': 'PASS' if correct_hyde['is_correct'] else 'FAIL',
            'status_multi': 'PASS' if correct_multi['is_correct'] else 'FAIL'
        }

        results.append(result)

    with open(OUTPUT_RESULTS, 'w') as f:
        json.dump(results, f, indent=2)




if __name__ == "__main__":
    main()