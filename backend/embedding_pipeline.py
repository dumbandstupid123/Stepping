from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import torch
import numpy as np
from langdetect import detect
from datetime import datetime

class EmbeddingPipeline:
    def __init__(self, model_name: str = "paraphrase-multilingual-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        
    def prepare_text_chunks(self, resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare text chunks from a resource for embedding generation."""
        chunks = []
        
        # Basic information chunk
        basic_info = f"Name: {resource['name']}\nCategory: {resource['category']}\n"
        if resource.get('notes'):
            basic_info += f"Notes: {resource['notes']}"
            
        chunks.append({
            'content_type': 'description',
            'text': basic_info,
            'language': 'en'  # Default language
        })
        
        # Requirements chunk
        if resource.get('requirements'):
            req_text = "Requirements: " + ", ".join(resource['requirements'])
            chunks.append({
                'content_type': 'requirements',
                'text': req_text,
                'language': 'en'
            })
            
        # Services chunk (if available)
        if resource.get('services'):
            services_text = "Services: " + ", ".join(resource['services'])
            chunks.append({
                'content_type': 'services',
                'text': services_text,
                'language': 'en'
            })
            
        return chunks
    
    def detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        try:
            return detect(text)
        except:
            return 'en'  # Default to English if detection fails
    
    def generate_embeddings(self, text: str) -> np.ndarray:
        """Generate embeddings for a given text."""
        with torch.no_grad():
            embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def process_resource(self, resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single resource and generate embeddings for all its chunks."""
        chunks = self.prepare_text_chunks(resource)
        embeddings = []
        
        for chunk in chunks:
            # Detect language if not already specified
            if 'language' not in chunk:
                chunk['language'] = self.detect_language(chunk['text'])
            
            # Generate embedding
            embedding = self.generate_embeddings(chunk['text'])
            
            # Create embedding record (resource_id will be set by caller)
            embedding_record = {
                'content_type': chunk['content_type'],
                'language': chunk['language'],
                'embedding': embedding.tolist(),
                'text_chunk': chunk['text'],
                'created_at': datetime.utcnow().isoformat()
            }
            
            embeddings.append(embedding_record)
            
        return embeddings
    
    def batch_process_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple resources in batch."""
        all_embeddings = []
        for resource in resources:
            embeddings = self.process_resource(resource)
            all_embeddings.extend(embeddings)
        return all_embeddings

# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = EmbeddingPipeline()
    
    # Example resource
    sample_resource = {
        "name": "Community Health Center",
        "category": "healthcare",
        "notes": "Provides primary care and mental health services",
        "requirements": ["ID", "Proof of address"],
        "services": ["Primary Care", "Mental Health", "Dental Care"]
    }
    
    # Process the resource
    embeddings = pipeline.process_resource(sample_resource)
    
    # Print results
    print(f"Generated {len(embeddings)} embeddings")
    for emb in embeddings:
        print(f"\nContent Type: {emb['content_type']}")
        print(f"Language: {emb['language']}")
        print(f"Text Chunk: {emb['text_chunk'][:100]}...")
        print(f"Embedding Shape: {len(emb['embedding'])}") 