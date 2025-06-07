#!/usr/bin/env python3

import numpy as np
from typing import List, Dict, Any
from db_interface import DatabaseInterface
from embedding_pipeline import EmbeddingPipeline

class ImprovedSearch:
    """Enhanced search with actual semantic similarity."""
    
    def __init__(self):
        self.db = DatabaseInterface()
        self.pipeline = EmbeddingPipeline()
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Handle zero vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (norm1 * norm2)
    
    def search_resources_semantic(self, query: str, top_k: int = 5, 
                                 category_filter: str = None) -> List[Dict[str, Any]]:
        """Perform actual semantic search using embeddings."""
        
        # Generate query embedding
        query_embedding = self.pipeline.generate_embeddings(query)
        
        # Get all resources and embeddings
        all_resources = self.db.get_all_resources()
        
        # Get embeddings collection
        embeddings_collection = self.db.db.get_collection('embeddings')
        all_embeddings = list(embeddings_collection.find({}))
        
        # Calculate similarities
        resource_scores = {}
        
        for embedding_doc in all_embeddings:
            resource_id = embedding_doc.get('resource_id')
            stored_embedding = embedding_doc.get('embedding', [])
            
            if len(stored_embedding) > 0 and resource_id:
                # Calculate similarity
                similarity = self.cosine_similarity(query_embedding.tolist(), stored_embedding)
                
                # Keep highest similarity score per resource
                if resource_id not in resource_scores or similarity > resource_scores[resource_id]:
                    resource_scores[resource_id] = similarity
        
        # Get resource details and apply filters
        scored_resources = []
        resource_lookup = {r.get('_id'): r for r in all_resources}
        
        for resource_id, score in resource_scores.items():
            if resource_id in resource_lookup:
                resource = resource_lookup[resource_id]
                
                # Apply category filter
                if category_filter and resource.get('category') != category_filter:
                    continue
                
                # Only include active resources
                if resource.get('status') != 'active':
                    continue
                
                scored_resources.append({
                    'resource_id': resource_id,
                    'name': resource.get('name', ''),
                    'category': resource.get('category', ''),
                    'address': resource.get('address', ''),
                    'phone': resource.get('phone', ''),
                    'services': resource.get('services', []),
                    'requirements': resource.get('requirements', []),
                    'cost': resource.get('cost', ''),
                    'hours_structured': resource.get('hours_structured', {}),
                    'website': resource.get('website', ''),
                    'notes': resource.get('notes', ''),
                    'score': score
                })
        
        # Sort by similarity score (highest first)
        scored_resources.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_resources[:top_k]
    
    def test_semantic_search(self):
        """Test the improved semantic search."""
        test_queries = [
            ("mental health counseling", None),
            ("food assistance", "food"),
            ("dental care", "dental"),
            ("substance abuse treatment", "substance_abuse"),
            ("emergency housing", "housing")
        ]
        
        print("🔍 Testing Improved Semantic Search")
        print("=" * 60)
        
        for query, category in test_queries:
            print(f"\n🗣️  Query: '{query}' (category: {category})")
            print("-" * 40)
            
            results = self.search_resources_semantic(query, top_k=3, category_filter=category)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result['name']} ({result['category']})")
                    print(f"   📍 {result['address']}")
                    print(f"   📞 {result['phone']}")
                    print(f"   🎯 Similarity: {result['score']:.3f}")
                    
                    if result['services']:
                        print(f"   🔧 Services: {', '.join(result['services'][:3])}")
                    print()
            else:
                print("   No results found")
    
    def close(self):
        """Close database connection."""
        self.db.close()

if __name__ == "__main__":
    search = ImprovedSearch()
    try:
        search.test_semantic_search()
    finally:
        search.close() 