from typing import List, Dict
from langchain_core.documents import Document
from web_page_loader import WebContentLoader
from data_chunking import DocumentChunker
from data_ingestion import VectorStore
from sentence_transformers import CrossEncoder
from groq import Groq


class RagPipeline:
    def __init__(
        self,
        embeddings,
        persist_directory: str = "data/chroma_db",
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ):
        # Step 1: Initialize modules
        self.loader = WebContentLoader()
        self.chunker = DocumentChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            save_dir="data/chunks",
            file_format="jsonl"
        )
        self.vector_store = VectorStore(
            embeddings=embeddings,
            persist_directory=persist_directory
        )
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.llm = Groq()

    # -----------------------
    def ingest_urls(self, urls: List[str]):
        all_docs = []

        self.loader.set_urls(urls)
        docs = self.loader.load_and_process()  # List[Document]

        # Chunk each document
        for doc in docs:
            safe_name = doc.metadata.get("source", "").split("//")[-1].replace("/", "_")
            chunks = self.chunker.create_chunks([doc], save_name=safe_name)
            all_docs.extend(chunks)

        # Store in ChromaDB (persistent)
        self.vector_store.create_store(all_docs, collection_name="travel")

    def rerank_documents(self, question, documents, top_k=5):
        if not documents:
            return []

        pairs = [(question, doc) for doc in documents]

        scores = self.reranker.predict(pairs)

        scored_docs = list(zip(documents, scores))

        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in scored_docs[:top_k]]
    
    def judge_context(self, query: str, documents: List[str]) -> str:
        # LLM prompt to judge context
        prompt = f"""
            You are a context quality judge in a Retrieval-Augmented Generation (RAG) system.

            Your task is to decide whether the retrieved context contains enough relevant
            information to reasonably answer the user's query.

            Guidelines:

            - If the context contains relevant information related to the query,
            even if not perfect or complete, return: context_good

            - If the context is mostly unrelated, empty, or missing key information,
            return: context_insufficient

            - For planning or recommendation queries, partial useful information is acceptable.

            Important:

            - Use ONLY the provided context
            - Do NOT assume external knowledge
            - Be practical, not overly strict
            - Default to context_good if the context is reasonably relevant

            Query:
            "{query}"

            Context:
            {documents}

            Answer ONLY one word:
            context_good
            context_insufficient
        """

        # Call LLM
        response = self.llm.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.5,
                max_tokens=100,
                messages=[{'role':'user','content':prompt}]
            )

        # Clean response
        raw_content = response.choices[0].message.content

        result = raw_content.strip()
        print(f"Context judgment response: {result}")
        if "context_good" in result:
            return "context_good"
        else:
            return "context_insufficient"
    
    def generate_final_answer(self, query: str, retrieved_docs: list, metadata: list) -> str:

        # Combine docs with metadata for context
        context_snippet = ""
        for doc, meta in zip(retrieved_docs, metadata):
            meta_info = ", ".join(f"{k}: {v}" for k, v in meta.items())
            context_snippet += f"[{meta_info}] {doc}\n"

        prompt = f"""
            You are an assistant that provides short, factual, concise answers based on
            the provided context. Use only the information from the context; do not
            make assumptions or hallucinate.
            If the user's query asks to plan, suggest, or instruct what to do, generate a structured response.

            Query: "{query}"

            Context:
            {context_snippet}

            Answer in a concise, to-the-point format (1-3 sentences), bullet-pointed if applicable. Cite any relevant
            source if possible using the metadata in brackets.
        """

        # Call LLM
        response = self.llm.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0.5,
                max_tokens=1024,
                messages=[{'role':'user','content':prompt}]
            )

        # Clean response
        raw_content = response.choices[0].message.content

        result = raw_content.strip()

        return result

    def query(self, query_text: str, top_k: int = 5) -> List[Document]:
        preferences = self.extract_preferences(query_text)
        # using preferences to create metdata filters for retrieval
        # Initialize empty list for conditions
        conditions = []

        # Add city filter if it's not None or empty
        city = preferences.get("city")
        if city:
            conditions.append({"city": city})

        # Add interests filter if list is not empty
        interests = preferences.get("interests", [])
        if interests:
            conditions.append({"interests": {"$in": interests}})

        # Add budget filter if it's not None or empty
        budget = preferences.get("budget")
        if budget:
            conditions.append({"price_level": budget})

        # Build final filter
        filters = {"$or": conditions} if conditions else None
        
        store = self.vector_store.get_vectorstore()
        results = store._collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=filters
        )

        # If no documents retrieved, return user friendly message
        if len(results["documents"][0]) == 0:
            return {
                "preferences": preferences,
                "filters": filters,
                "judgment": "context_insufficient",
                "retrieved_docs": 0,
                "final_answer": "No relevant information found based on your query and preferences. We don't have enough information to answer your question accurately."
            }
        
        # rerank documents based on query and metadata
        retrieved_docs = results["documents"][0]
        retrieved_metadatas = results["metadatas"][0]
        combined_docs = []

        for doc, meta in zip(retrieved_docs, retrieved_metadatas):
            meta_info = ", ".join(f"{k}: {v}" for k, v in meta.items())
            combined_docs.append(
                f"Content: {doc}\nMetadata: {meta_info}"
            )

        reranked_docs = self.rerank_documents(query_text, combined_docs, top_k=5)
        
        # Judge context sufficiency
        judgment = self.judge_context(query_text, reranked_docs)
        print(f"Context judgment: {judgment}")

        if judgment == "context_insufficient":
            # User friedly message instead of returning empty list
            return {
                "preferences": preferences,
                "filters": filters,
                "judgment": judgment,
                "retrieved_docs": len(reranked_docs),
                "final_answer": "The retrieved information is insufficient to answer your query accurately. Please try rephrasing your question or providing more details."
            }
        
        # Generate final answer using LLM
        final_answer = self.generate_final_answer(query_text, reranked_docs, results["metadatas"][0])

        final_result = {
            "preferences": preferences,
            "filters": filters,
            "judgment": judgment,
            "retrieved_docs": len(reranked_docs),
            "final_answer": final_answer
        }

        return final_result

    def extract_preferences(self, query_text: str) -> dict:
        prompt = f"""
    
            You are an AI assistant. You must ONLY respond with valid JSON.
            Do NOT include explanations, notes, or text outside the JSON object.

            Task:  Extract metadata from the following travel text. Return as JSON with keys: city, interests, budget.
            Text: {query_text}

            JSON Schema:
                "city": "<city>",
                "interests": ["<interest1>", "<interest2>", ...],
                "budget": "<high | medium | cheap>"

            Rules:
            1. Only return JSON. Any text outside JSON will be considered invalid.
            2. Always include all fields.
            3. Do not use comments, extra newlines, or formatting outside JSON.
            4. If information is missing, use "null" or empty array as placeholder.

            Provide the JSON strictly according to the schema.
        """

        try:
            
            response = self.llm.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                temperature=0,
                max_tokens=100,
                messages=[{'role':'user','content':prompt}]
            )
            import json
            print(f"Groq LLM response for metadata extraction: {response}")
  
            raw_content = response.choices[0].message.content

            clean_content = raw_content.strip()
            if clean_content.startswith("```") and clean_content.endswith("```"):
                clean_content = "\n".join(clean_content.splitlines()[1:-1])

            # Now load as JSON
            preferences = json.loads(clean_content)
        except Exception as e:
            print(f"Error extracting preferences: {e}")
            preferences = {}
        return preferences