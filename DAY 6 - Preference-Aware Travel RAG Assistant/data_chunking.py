from typing import List, Optional, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import json
import uuid


class DocumentChunker:
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        save_dir: Optional[str] = "data/chunks",
        file_format: str = "jsonl"
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if file_format not in ("json", "jsonl"):
            raise ValueError("file_format must be 'json' or 'jsonl'")

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.save_dir = save_dir
        self.file_format = file_format

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)

    def clean_text(self, text: str) -> str:
        text = text.replace("\n", " ")
        text = " ".join(text.split())
        return text

    def create_chunks(
        self,
        documents: List[Document],
        save_name: Optional[str] = None
    ) -> List[Document]:

        cleaned_docs = [
            Document(
                page_content=self.clean_text(doc.page_content),
                metadata=doc.metadata
            )
            for doc in documents
        ]

        # Split into chunks
        chunks = self.splitter.split_documents(cleaned_docs)
        print(f"Created {len(chunks)} chunks from {len(documents)} documents")

        # Save if requested
        if save_name and self.save_dir:
            self._save_chunks(chunks, save_name)

        return chunks

    def _save_chunks(self, chunks: List[Document], file_name: str):
        """Save chunks to JSON or JSONL file."""
        file_path = os.path.join(self.save_dir, f"{file_name}.{self.file_format}")

        if self.file_format == "json":
            data = [
                {
                    "id": str(uuid.uuid4()),
                    "text": chunk.page_content,
                    "metadata": chunk.metadata
                }
                for chunk in chunks
            ]
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        elif self.file_format == "jsonl":
            with open(file_path, "w", encoding="utf-8") as f:
                for chunk in chunks:
                    entry = {
                        "id": str(uuid.uuid4()),
                        "text": chunk.page_content,
                        "metadata": chunk.metadata
                    }
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print(f"Saved {len(chunks)} chunks to {file_path}")