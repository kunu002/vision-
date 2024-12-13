# embedding.py
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Any
import torch
from text_extraction import LANGUAGE_MAP

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

def chunk_text(text: str, chunk_size: int = 1000) -> List[str]:
    """
    Split text into smaller chunks while preserving sentence boundaries
    """
    import re
    sentences = re.split('(?<=[।.!?॥])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length
            
    if current_chunk:
        chunks.append(' '.join(current_chunk))
        
    return chunks

def embed_text(text_dict: Dict[str, str], input_language: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Embed text and return both embeddings and their corresponding text chunks
    with language information preserved
    """
    embedded_dict = {}
    
    # Set larger batch size for efficiency
    batch_size = 32
    
    for page, text in text_dict.items():
        chunks = chunk_text(text)
        page_chunks = []
        
        # Process chunks in batches
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            
            # Generate embeddings for the batch
            try:
                embeddings = model.encode(batch_chunks, 
                                       batch_size=batch_size,
                                       show_progress_bar=False,
                                       normalize_embeddings=True)  # Normalize for better cross-lingual matching
                
                for chunk, embedding in zip(batch_chunks, embeddings):
                    page_chunks.append({
                        'text': chunk,
                        'embedding': embedding,
                        'language': input_language
                    })
            except Exception as e:
                print(f"Error encoding batch: {str(e)}")
                continue
            
        embedded_dict[page] = page_chunks
        
    return embedded_dict