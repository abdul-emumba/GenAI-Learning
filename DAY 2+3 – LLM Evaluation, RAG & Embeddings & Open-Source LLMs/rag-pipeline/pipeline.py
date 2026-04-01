import json
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
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
GOLDEN_DATASET_PATH = "data/golden_dataset.json"
OUTPUT_RESULTS = "rag_results.json"

model = SentenceTransformer('all-MiniLM-L6-v2')
client = Groq()
print("Groq client initialized successfully.")

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
                doc.metadata["source"] = path
            documents.extend(docs)
        return documents


class TextProcessor:
    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
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
    def __init__(self, vectordb, model_name="openai/gpt-oss-120b"):
        self.retriever = vectordb.as_retriever(search_kwargs={"k": 3})
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
    def __init__(self, pdf_paths):
        self.pdf_paths = pdf_paths
        self.qa_engine = None

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
        vectordb = vector_manager.create_store(chunks)

        print("Initializing QA engine...")
        self.qa_engine = QAEngine(vectordb)

        print("RAG Pipeline Ready!")

    def query(self, question, answer_type):
        if not self.qa_engine:
            raise Exception("Pipeline not built. Call build() first.")
        return self.qa_engine.ask(question, answer_type)
    

def run_model(model_name, prompt, answer_type=None, system_prompt='You are a helpful assistant.'):
    if answer_type == 'factual':
        dev_inst = "Answer factually based on the context."
    elif answer_type == 'reasoning':
        dev_inst = "Provide a reasoned explanation based on the context."
    elif answer_type == 'negative':
        dev_inst = "If the information is not mentioned in the context, state 'Not mentioned in the document.' Otherwise, answer based on the context."
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
        "pdfs/djangobook.pdf",
        "pdfs/pythonprogramming.pdf"
    ]

    pipeline = RAGPipeline(pdfs)
    pipeline.build()

    dataset = load_dataset(GOLDEN_DATASET_PATH)
    results = []

    for row in dataset:
        question = row['question']
        ground_truth = row['ground_truth']
        answer_type = row['answer_type']

        print(f"Question: {question}")

        answer = pipeline.query(question, answer_type=answer_type)

        correct = is_correct(answer, ground_truth)

        result = {
            'question': question,
            'ground_truth': ground_truth,
            'answer': answer,
            'correct': correct['is_correct'],
            'similarity': correct['similarity'],
            'status': 'PASS' if correct['is_correct'] else 'FAIL'
        }

        results.append(result)

    with open(OUTPUT_RESULTS, 'w') as f:
        json.dump(results, f, indent=2)




if __name__ == "__main__":
    main()