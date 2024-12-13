# database.py
import faiss
import numpy as np
from typing import Dict, List, Any

class DocumentStore:
    def __init__(self):
        self.index = None
        self.text_chunks: Dict[int, Dict[str, Any]] = {}
        self.current_id = 0
    
    def add_to_database(self, embedded_dict: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Add embeddings and their corresponding text to the database
        Expected format of embedded_dict:
        {
            page_num: [
                {
                    'text': chunk_text,
                    'embedding': chunk_embedding,
                    'language': chunk_language
                },
            ]
        }
        """
        for page, chunks in embedded_dict.items():
            embeddings = []
            for chunk in chunks:
                embeddings.append(chunk['embedding'])
                self.text_chunks[self.current_id] = {
                    'text': chunk['text'],
                    'language': chunk['language']
                }
                self.current_id += 1
            
            embeddings_array = np.array(embeddings)
            
            if self.index is None and len(embeddings) > 0:
                dimension = embeddings_array.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
            
            if len(embeddings) > 0:
                self.index.add(embeddings_array)
    
    def search_database(self, query_embedding: np.ndarray, k: int = 3) -> List[Dict[str, Any]]:

        if self.index is None:
            return []
            
        D, I = self.index.search(np.array([query_embedding]), k)
        
        relevant_chunks = [
            {
                'text': self.text_chunks[idx]['text'],
                'language': self.text_chunks[idx]['language']
            } for idx in I[0] if idx in self.text_chunks
        ]
        return relevant_chunks

document_store = DocumentStore()