from embedding_pipeline import EmbeddingPipeline
from db_interface import DatabaseInterface
import uuid
from datetime import datetime
import json

def process_and_store_resource(resource_data: dict, pipeline: EmbeddingPipeline, db: DatabaseInterface):
    """Process a single resource and store it in the database."""
    # Insert resource into database (db.insert_resource generates its own UUID)
    resource_id = db.insert_resource(resource_data)
    
    # Generate embeddings
    embeddings = pipeline.process_resource(resource_data)
    
    # Store embeddings
    for embedding in embeddings:
        embedding['resource_id'] = resource_id
        db.insert_embedding(embedding)
    
    return resource_id

def main():
    # Initialize components
    print("Initializing embedding pipeline...")
    pipeline = EmbeddingPipeline()
    
    print("Connecting to database...")
    db = DatabaseInterface()
    
    # Example resource
    sample_resource = {
        "name": "Community Health Center",
        "category": "healthcare",
        "address": "123 Main St, City, State 12345",
        "phone": "(555) 123-4567",
        "hours_structured": {
            "monday": "9:00-17:00",
            "tuesday": "9:00-17:00",
            "wednesday": "9:00-17:00",
            "thursday": "9:00-17:00",
            "friday": "9:00-17:00",
            "saturday": "closed",
            "sunday": "closed"
        },
        "requirements": ["ID", "Proof of address", "Insurance card"],
        "languages": ["en", "es"],
        "notes": "Provides primary care, mental health services, and dental care. Sliding scale available.",
        "verified_at": datetime.utcnow().isoformat(),
        "status": "active"
    }
    
    try:
        # Process and store the resource
        print("Processing and storing resource...")
        resource_id = process_and_store_resource(sample_resource, pipeline, db)
        print(f"✅ Successfully processed and stored resource with ID: {resource_id}")
        
        # Example search
        print("\nTesting semantic search...")
        query_text = "Where can I get mental health services?"
        query_embedding = pipeline.generate_embeddings(query_text)
        
        results = db.search_similar(
            query_embedding,
            filters={'category': 'healthcare'}
        )
        
        print(f"\nSearch Results for: '{query_text}'")
        print("-" * 50)
        
        if results:
            for i, r in enumerate(results, 1):
                print(f"{i}. Name: {r['name']}")
                print(f"   Category: {r['category']}")
                print(f"   Status: {r['status']}")
                print(f"   Similarity: {r['similarity']:.4f}")
                print()
        else:
            print("No results found.")
            
        # Show all resources in database
        print("All resources in database:")
        all_resources = db.get_all_resources()
        for resource in all_resources:
            print(f"- {resource.get('name')} ({resource.get('category')})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main() 