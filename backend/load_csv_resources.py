import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any, List
from db_interface import DatabaseInterface
from embedding_pipeline import EmbeddingPipeline

class ResourceCSVLoader:
    def __init__(self):
        self.pipeline = EmbeddingPipeline()
        self.db = DatabaseInterface()
        
    def parse_coordinates(self, coord_str: str) -> Dict[str, float]:
        """Parse coordinate string into lat/lng dict."""
        if not coord_str or coord_str.strip() == "":
            return {}
        try:
            lat, lng = coord_str.split(',')
            return {
                "latitude": float(lat.strip()),
                "longitude": float(lng.strip())
            }
        except:
            return {}
    
    def parse_hours(self, hours_str: str) -> Dict[str, str]:
        """Parse hours string into structured format."""
        if not hours_str or hours_str.strip() == "{}":
            return {}
        try:
            return json.loads(hours_str)
        except:
            return {}
    
    def parse_list_field(self, field_str: str) -> List[str]:
        """Parse comma-separated string into list."""
        if not field_str or field_str.strip() == "":
            return []
        return [item.strip() for item in field_str.split(',') if item.strip()]
    
    def clean_resource_data(self, row: pd.Series) -> Dict[str, Any]:
        """Clean and structure resource data from CSV row."""
        
        # Handle missing header row issue
        if pd.isna(row.iloc[0]) or row.iloc[0] == "name":
            return None
            
        resource = {
            "name": str(row.iloc[0]).strip(),
            "category": str(row.iloc[1]).strip(),
            "address": str(row.iloc[2]).strip(),
            "phone": str(row.iloc[3]).strip() if not pd.isna(row.iloc[3]) else "",
            "coordinates": self.parse_coordinates(str(row.iloc[4]) if not pd.isna(row.iloc[4]) else ""),
            "hours_structured": self.parse_hours(str(row.iloc[5]) if not pd.isna(row.iloc[5]) else "{}"),
            "services": self.parse_list_field(str(row.iloc[6]) if not pd.isna(row.iloc[6]) else ""),
            "requirements": self.parse_list_field(str(row.iloc[7]) if not pd.isna(row.iloc[7]) else ""),
            "cost": str(row.iloc[8]).strip() if not pd.isna(row.iloc[8]) else "",
            "eligibility": str(row.iloc[9]).strip() if not pd.isna(row.iloc[9]) else "",
            "accessibility": str(row.iloc[10]).strip() if not pd.isna(row.iloc[10]) else "",
            "appointment_required": str(row.iloc[11]).strip() if not pd.isna(row.iloc[11]) else "",
            "website": str(row.iloc[12]).strip() if not pd.isna(row.iloc[12]) else "",
            "status": str(row.iloc[13]).strip() if not pd.isna(row.iloc[13]) else "active",
            "verified_at": datetime.utcnow().isoformat(),
            "languages": ["en"]  # Default to English, can be enhanced
        }
        
        # Clean empty fields
        for key, value in resource.items():
            if value == "nan" or value == "":
                if key in ["services", "requirements", "languages"]:
                    resource[key] = []
                elif key == "coordinates":
                    resource[key] = {}
                elif key == "hours_structured":
                    resource[key] = {}
                else:
                    resource[key] = ""
        
        return resource
    
    def load_resources(self, csv_path: str = "resources.csv") -> Dict[str, int]:
        """Load resources from CSV file."""
        print(f"🚀 Starting resource loading from {csv_path}...")
        
        try:
            # Read CSV without headers since format varies
            df = pd.read_csv(csv_path, header=None)
            print(f"📊 Found {len(df)} rows to process")
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return {"success": 0, "failed": 0, "skipped": 0}
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            try:
                # Clean and structure the data
                resource_data = self.clean_resource_data(row)
                
                if resource_data is None:
                    skipped_count += 1
                    print(f"⏭️  Skipped row {index + 1} (header or empty)")
                    continue
                
                if not resource_data.get("name"):
                    skipped_count += 1
                    print(f"⏭️  Skipped row {index + 1} (no name)")
                    continue
                
                # Insert resource into database
                resource_id = self.db.insert_resource(resource_data)
                
                # Generate and store embeddings
                embeddings = self.pipeline.process_resource(resource_data)
                for embedding in embeddings:
                    embedding['resource_id'] = resource_id
                    self.db.insert_embedding(embedding)
                
                success_count += 1
                print(f"✅ {resource_data['name']} ({resource_data['category']})")
                
            except Exception as e:
                failed_count += 1
                resource_name = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else f"Row {index + 1}"
                print(f"❌ Failed to process {resource_name}: {e}")
        
        # Report results
        print(f"\n📈 Loading completed:")
        print(f"   ✅ Successfully loaded: {success_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        print(f"   📊 Total processed: {success_count + failed_count + skipped_count}")
        
        return {
            "success": success_count,
            "failed": failed_count,
            "skipped": skipped_count
        }
    
    def verify_loaded_data(self):
        """Verify what data was loaded into the database."""
        print("\n🔍 Verifying loaded data...")
        
        try:
            resources = self.db.get_all_resources()
            
            # Group by category
            categories = {}
            for resource in resources:
                category = resource.get('category', 'unknown')
                if category not in categories:
                    categories[category] = []
                categories[category].append(resource.get('name', 'Unknown'))
            
            print(f"\n📋 Database contains {len(resources)} resources:")
            for category, names in categories.items():
                print(f"   🏷️  {category.title()}: {len(names)} resources")
                for name in names[:3]:  # Show first 3
                    print(f"      - {name}")
                if len(names) > 3:
                    print(f"      ... and {len(names) - 3} more")
                    
        except Exception as e:
            print(f"❌ Error verifying data: {e}")
    
    def test_search(self, query: str = "food assistance"):
        """Test the search functionality with loaded data."""
        print(f"\n🔍 Testing search with query: '{query}'")
        
        try:
            from process_resources import search_resources
            results = search_resources(query, top_k=5)
            
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['name']} ({result['category']})")
                print(f"      Score: {result['score']:.3f}")
                print(f"      Address: {result['address']}")
                
        except Exception as e:
            print(f"❌ Search test failed: {e}")
    
    def close(self):
        """Close database connection."""
        self.db.close()

def main():
    """Main function to load resources."""
    loader = ResourceCSVLoader()
    
    try:
        # Load the resources
        results = loader.load_resources("resources.csv")
        
        if results["success"] > 0:
            # Verify the loaded data
            loader.verify_loaded_data()
            
            # Test search functionality
            loader.test_search("mental health services")
            loader.test_search("food pantry")
            loader.test_search("dental care")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        loader.close()

if __name__ == "__main__":
    main() 