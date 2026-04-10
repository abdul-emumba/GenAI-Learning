from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
import os

class VectorStore:
    def __init__(self, embeddings, persist_directory: str = "data/chroma_db"):
        self.embeddings = embeddings
        self.persist_directory = persist_directory
        self.vectorstore: Optional[Chroma] = None

        os.makedirs(persist_directory, exist_ok=True)

    def create_store(self, documents: List[Document], collection_name: str = "travel") -> Chroma:
        
        print(f"Creating new Chroma collection '{collection_name}' with {len(documents)} documents")
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            collection_name=collection_name,
            persist_directory=self.persist_directory
        )
        self.vectorstore.persist()  # Save to disk

        return self.vectorstore

    def add_documents(self, documents: List[Document], collection_name: str = "travel"):
        if not self.vectorstore:
            # Load existing collection
            self.vectorstore = Chroma(
                collection_name=collection_name,
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

        print(f"Adding {len(documents)} documents to collection '{collection_name}'")
        self.vectorstore.add_documents(documents)
        self.vectorstore.persist()

    def get_vectorstore(self, collection_name: str = "travel") -> Chroma:
        if not self.vectorstore:
            # If collection already exists, load it
            if os.path.exists(self.persist_directory):
                print(f"Loading existing Chroma collection '{collection_name}'")
                self.vectorstore = Chroma(
                    collection_name=collection_name,
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )

                return self.vectorstore
            
            raise ValueError("No collection found. Please create or load a collection first.")