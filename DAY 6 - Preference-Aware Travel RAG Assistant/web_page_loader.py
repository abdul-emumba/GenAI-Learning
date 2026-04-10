from typing import List, Dict
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader
from groq import Groq

class WebContentLoader:
    """
    Loads web pages one by one and extracts metadata using Groq LLM (llama-3.1-8b-instant).
    """

    def __init__(self, urls: List[str] = None):
        self.urls = urls or []
        # Initialize Groq generic client with model
        self.llm = Groq()

    def set_urls(self, urls: List[str]):
        """Set or update URLs dynamically"""
        self.urls = urls

    # -----------------------
    def load_and_process(self) -> List[Document]:
        """Load URLs one by one, extract metadata, and return Documents"""
        all_docs = []
        print(f"Ingesting {self.urls} URLs...")
        try:
            loader = WebBaseLoader(self.urls)
            docs = loader.load()  # returns list of Document

            for doc in docs:
                print(f"Processing document from URL: {doc.metadata}")
                metadata = self.build_metadata(doc.page_content, "url")
                doc.metadata.update(metadata)
                all_docs.append(doc)

        except Exception as e:  
            print(f"Error Ingesting URLs: {e}")

        print(f"Total documents loaded: {len(all_docs)}")
        return all_docs

    # -----------------------
    def build_metadata(self, text: str, url: str) -> Dict:
        """
        Use Groq LLM to extract minimal metadata:
        - city (write only the city name, no country or extra text, if multiple cities are mentioned, return the most relevant one)
        - category (food/art/sightseeing/other)
        - price_level (cheap/medium/expensive)
        """
        prompt = f"""
    
            You are an AI assistant. You must ONLY respond with valid JSON.
            Do NOT include explanations, notes, or text outside the JSON object.

            Task:  Extract metadata from the following travel text. Return as JSON with keys: city, category, interests, price_level.
            Text: {text}

            JSON Schema:
                "city": "<city>",
                "category": "< food | art | sightseeing | other>",
                "interests": ["<interest1>", "<interest2>", ...] (it can be the com),
                "price_level": "<high | medium | cheap>"

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
            metadata = json.loads(clean_content)
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            metadata = {}
        return metadata
    