import os
import json
import faiss
import numpy as np
from openai import OpenAI
from docx import Document
from typing import List, Dict
import pickle

class RAGSystem:
    def __init__(self, openai_api_key: str, knowledge_base_path: str = "RAG Source File.docx"):
        """Initialize RAG system with OpenAI embeddings and FAISS"""
        self.client = OpenAI(api_key=openai_api_key)
        self.knowledge_base_path = knowledge_base_path
        self.index = None
        self.chunks = []
        self.embedding_dim = 1536  # text-embedding-3-small dimension

        # Load or create vector database
        if os.path.exists("faiss_index.pkl") and os.path.exists("chunks.pkl"):
            self.load_index()
        else:
            self.build_index()

    def extract_text_from_docx(self) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(self.knowledge_base_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            return "\n".join(full_text)
        except Exception as e:
            print(f"Error reading document: {e}")
            return ""

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI"""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def build_index(self):
        """Build FAISS index from knowledge base"""
        print("Building FAISS index from knowledge base...")

        # Extract and chunk text
        text = self.extract_text_from_docx()
        if not text:
            print("Warning: No text extracted from document")
            return

        self.chunks = self.chunk_text(text)
        print(f"Created {len(self.chunks)} chunks")

        # Create embeddings
        embeddings = []
        for i, chunk in enumerate(self.chunks):
            print(f"Processing chunk {i+1}/{len(self.chunks)}")
            embedding = self.get_embedding(chunk)
            embeddings.append(embedding)

        # Build FAISS index
        embeddings_array = np.array(embeddings).astype('float32')
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.index.add(embeddings_array)

        # Save index and chunks
        self.save_index()
        print("FAISS index built and saved successfully!")

    def save_index(self):
        """Save FAISS index and chunks to disk"""
        faiss.write_index(self.index, "faiss_index.bin")
        with open("faiss_index.pkl", "wb") as f:
            pickle.dump({"index_path": "faiss_index.bin"}, f)
        with open("chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)

    def load_index(self):
        """Load FAISS index and chunks from disk"""
        print("Loading existing FAISS index...")
        self.index = faiss.read_index("faiss_index.bin")
        with open("chunks.pkl", "rb") as f:
            self.chunks = pickle.load(f)
        print(f"Loaded index with {len(self.chunks)} chunks")

    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Search for relevant chunks using query"""
        if not self.index or not self.chunks:
            return []

        # Get query embedding
        query_embedding = self.get_embedding(query)
        query_vector = np.array([query_embedding]).astype('float32')

        # Search in FAISS
        distances, indices = self.index.search(query_vector, top_k)

        # Return relevant chunks
        results = [self.chunks[idx] for idx in indices[0] if idx < len(self.chunks)]
        return results

    def get_context(self, query: str) -> str:
        """Get context for query from knowledge base"""
        relevant_chunks = self.search(query, top_k=3)
        if not relevant_chunks:
            return ""

        context = "\n\n".join(relevant_chunks)
        return f"Relevant information from knowledge base:\n{context}"
