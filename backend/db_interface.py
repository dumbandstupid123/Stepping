from astrapy import DataAPIClient
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

class DatabaseInterface:
    def __init__(self):
        """Initialize database interface using astrapy REST API."""
        # Use astrapy REST API
        self.client = DataAPIClient(os.getenv('ASTRA_API_TOKEN'))
        self.db = self.client.get_database(os.getenv('ASTRA_API_ENDPOINT'))
        
        # Create collections if they don't exist
        self.create_collections()
    
    def create_collections(self):
        """Create collections if they don't exist."""
        try:
            # Create resources collection
            self.db.create_collection('resources')
        except Exception:
            pass  # Collection might already exist
        
        try:
            # Create embeddings collection
            self.db.create_collection('embeddings')
        except Exception:
            pass  # Collection might already exist
    
    def insert_resource(self, resource: Dict[str, Any]) -> str:
        """Insert a new resource and return its ID."""
        resource_id = str(uuid.uuid4())
        
        # Get resources collection
        collection = self.db.get_collection('resources')
        
        # Prepare resource document
        resource_doc = {
            '_id': resource_id,
            'name': resource['name'],
            'category': resource['category'],
            'address': resource.get('address'),
            'coordinates': resource.get('coordinates'),
            'phone': resource.get('phone'),
            'hours_structured': resource.get('hours_structured', {}),
            'hours_text': resource.get('hours_text'),
            'requirements': resource.get('requirements', []),
            'languages': resource.get('languages', []),
            'notes': resource.get('notes'),
            'verified_at': resource.get('verified_at'),
            'status': resource.get('status', 'pending'),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Insert resource
        collection.insert_one(resource_doc)
        
        return resource_id
    
    def insert_embedding(self, embedding: Dict[str, Any]):
        """Insert a new embedding."""
        # Get embeddings collection
        collection = self.db.get_collection('embeddings')
        
        # Prepare embedding document
        embedding_doc = {
            '_id': str(uuid.uuid4()),
            'resource_id': embedding['resource_id'],
            'content_type': embedding['content_type'],
            'language': embedding['language'],
            'embedding': embedding['embedding'],
            'text_chunk': embedding['text_chunk'],
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Insert embedding
        collection.insert_one(embedding_doc)
    
    def search_similar(self, query_embedding: List[float], 
                      limit: int = 5,
                      filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar resources."""
        # Get resources collection
        collection = self.db.get_collection('resources')
        
        # Build filter
        filter_dict = {'status': 'active'}
        if filters and 'category' in filters:
            filter_dict['category'] = filters['category']
        
        # Execute query
        results = collection.find(filter_dict, limit=limit)
        
        return [{
            'resource_id': r.get('_id'),
            'name': r.get('name'),
            'category': r.get('category'),
            'status': r.get('status'),
            'similarity': 1.0  # Placeholder for similarity score
        } for r in results]
    
    def get_all_resources(self) -> List[Dict[str, Any]]:
        """Get all resources from the database."""
        collection = self.db.get_collection('resources')
        results = collection.find({})
        return list(results)
    
    def close(self):
        """Close the database connection."""
        pass  # astrapy doesn't need explicit closing

# Example usage
if __name__ == "__main__":
    print("Testing DataStax Astra DB connection...")
    try:
        db = DatabaseInterface()
        print("✅ Database connection successful!")
        
        # Test getting all resources
        resources = db.get_all_resources()
        print(f"Found {len(resources)} existing resources")
        
        # Test inserting a sample resource
        sample_resource = {
            'name': 'Test Health Center',
            'category': 'healthcare',
            'address': '123 Test St',
            'phone': '(555) 123-4567',
            'status': 'active',
            'notes': 'Test resource for verification'
        }
        
        resource_id = db.insert_resource(sample_resource)
        print(f"✅ Sample resource inserted with ID: {resource_id}")
        
        # Test search
        results = db.search_similar(
            [0.1] * 768,  # Dummy embedding
            filters={'category': 'healthcare'}
        )
        print(f"✅ Search test completed, found {len(results)} results")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Database test failed: {e}") 