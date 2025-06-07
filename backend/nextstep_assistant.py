#!/usr/bin/env python3

import json
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os
from dotenv import load_dotenv

from db_interface import DatabaseInterface
from embedding_pipeline import EmbeddingPipeline

# You can use OpenAI, Anthropic, or local models
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

load_dotenv()

@dataclass
class SearchResult:
    """Structure for search results."""
    name: str
    category: str
    address: str
    phone: str
    services: List[str]
    requirements: List[str]
    cost: str
    hours: Dict[str, str]
    website: str
    notes: str
    score: float

class NextStepAssistant:
    """RAG-powered healthcare assistant for Houston resources."""
    
    def __init__(self, use_openai: bool = True):
        """Initialize the assistant with database and LLM connections."""
        self.db = DatabaseInterface()
        self.pipeline = EmbeddingPipeline()
        self.use_openai = use_openai and HAS_OPENAI
        
        if self.use_openai and os.getenv('OPENAI_API_KEY'):
            openai.api_key = os.getenv('OPENAI_API_KEY')
    
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
        
    def search_resources(self, query: str, top_k: int = 5, 
                        category_filter: str = None) -> List[SearchResult]:
        """Search for relevant resources using semantic similarity."""
        
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
        search_results = []
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
                
                search_result = SearchResult(
                    name=resource.get('name', ''),
                    category=resource.get('category', ''),
                    address=resource.get('address', ''),
                    phone=resource.get('phone', ''),
                    services=resource.get('services', []),
                    requirements=resource.get('requirements', []),
                    cost=resource.get('cost', ''),
                    hours=resource.get('hours_structured', {}),
                    website=resource.get('website', ''),
                    notes=resource.get('notes', ''),
                    score=score
                )
                search_results.append(search_result)
        
        # Sort by similarity score (highest first)
        search_results.sort(key=lambda x: x.score, reverse=True)
        
        return search_results[:top_k]
    
    def format_hours(self, hours: Dict[str, str]) -> str:
        """Format hours dictionary into readable text."""
        if not hours:
            return "Hours not specified"
        
        formatted = []
        for day, time in hours.items():
            if time.lower() != "closed":
                formatted.append(f"{day.title()}: {time}")
        
        return "; ".join(formatted) if formatted else "Hours not specified"
    
    def generate_response_openai(self, query: str, resources: List[SearchResult]) -> str:
        """Generate response using OpenAI GPT."""
        
        # Prepare context from search results
        context = "Available resources:\n\n"
        for i, resource in enumerate(resources, 1):
            context += f"{i}. **{resource.name}** ({resource.category})\n"
            context += f"   📍 Address: {resource.address}\n"
            context += f"   📞 Phone: {resource.phone}\n"
            
            if resource.services:
                context += f"   🔧 Services: {', '.join(resource.services)}\n"
            
            if resource.requirements:
                context += f"   📋 Requirements: {', '.join(resource.requirements)}\n"
            
            if resource.cost:
                context += f"   💰 Cost: {resource.cost}\n"
            
            if resource.hours:
                context += f"   🕐 Hours: {self.format_hours(resource.hours)}\n"
            
            if resource.website:
                context += f"   🌐 Website: {resource.website}\n"
            
            if resource.notes:
                context += f"   📝 Notes: {resource.notes}\n"
            
            context += f"   🎯 Relevance: {resource.score:.1%}\n\n"
        
        # Create prompt
        prompt = f"""You are a caring, empathetic social worker helping someone in Houston who asked: "{query}"

I want you to respond as if you're sitting across from this person, offering genuine support and practical help. Be warm, understanding, and encouraging while providing clear, actionable guidance.

Based on these resources, please:

1. **Start with empathy** - Acknowledge their situation with warmth and understanding
2. **Provide hope** - Let them know help is available and they've taken a good step by reaching out
3. **Give specific recommendations** - Clearly list the best resources with all the important details
4. **Offer practical next steps** - Tell them exactly what to do next (call, visit, bring documents, etc.)
5. **Be encouraging** - End with reassurance and remind them you're here to help

{context}

Respond in a conversational, caring tone as if you're a social worker who genuinely wants to help this person succeed. Include all the contact information and practical details they need, but present it in a warm, human way.

Remember: This person may be scared, overwhelmed, or vulnerable. Your response should make them feel heard, supported, and hopeful."""

        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a compassionate social worker in Houston, Texas. You provide empathetic, practical help to people seeking healthcare and social services. Your responses should be warm, caring, and professionally supportive while being informative and actionable."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=900,
                temperature=0.8
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self.generate_response_local(query, resources)
    
    def generate_response_local(self, query: str, resources: List[SearchResult]) -> str:
        """Generate response using local templates (fallback) with social worker tone."""
        
        if not resources:
            return f"""I hear you asking about "{query}" and I want you to know that you're not alone in this. It takes courage to reach out for help, and I'm proud of you for taking this step.

While I don't have specific resources that match exactly what you're looking for right now, there are still wonderful people ready to help you:

**🤝 Immediate Support:**
- **Call 211** - Just dial 2-1-1 and speak with a caring counselor who can connect you with resources in your area
- **Harris Health System** - Call (713) 634-1110 for healthcare services with sliding scale fees
- **United Way** - Visit 211texas.org for a comprehensive database of local resources

Sometimes finding the right help takes a few tries, and that's completely normal. Don't give up - the right support is out there for you.

Is there a more specific type of service you're looking for? I'd love to help you narrow down the search so we can find exactly what you need. You deserve support, and we're going to find it together. 💙"""

        # Create empathetic opening based on query type
        empathy_responses = {
            'mental health': "I can see you're reaching out for mental health support, and that takes real strength. Mental health is just as important as physical health, and seeking help shows wisdom and self-care.",
            'food': "I understand that food security is a basic need, and it's completely understandable to seek help when things are tight. There's no shame in needing assistance - we all need support sometimes.",
            'housing': "Housing challenges can feel overwhelming, but you're taking the right step by looking for help. Safe, stable housing is a fundamental need, and there are people ready to support you.",
            'dental': "Dental pain and oral health concerns can really impact your quality of life. I'm glad you're seeking care - your health matters, and you deserve to feel comfortable and pain-free.",
            'substance': "Reaching out for help with substance use shows incredible courage and strength. Recovery is a journey, and there are compassionate professionals ready to walk alongside you.",
            'healthcare': "Healthcare can feel complicated and expensive, but everyone deserves access to quality care. Let me help you find some options that might work for your situation."
        }
        
        # Choose appropriate empathy response
        empathy = "I'm so glad you reached out for help today. That takes courage, and you should be proud of yourself for taking this important step."
        for key, response in empathy_responses.items():
            if key in query.lower():
                empathy = response
                break
        
        response = f"{empathy}\n\n**Here are some excellent resources I found for you:**\n\n"
        
        for i, resource in enumerate(resources[:3], 1):  # Top 3 results
            response += f"**{i}. {resource.name}** ✨ {resource.score:.0%} match\n"
            response += f"   📍 **Location:** {resource.address}\n"
            response += f"   📞 **Phone:** {resource.phone}\n"
            
            if resource.requirements:
                response += f"   📋 **What to bring:** {', '.join(resource.requirements)}\n"
            
            if resource.cost:
                response += f"   💰 **Cost:** {resource.cost}\n"
            
            if resource.hours:
                response += f"   🕐 **Hours:** {self.format_hours(resource.hours)}\n"
            
            if resource.services:
                services_list = ', '.join(resource.services[:3])
                if len(resource.services) > 3:
                    services_list += f" and {len(resource.services) - 3} more services"
                response += f"   🔧 **Services:** {services_list}\n"
            
            response += "\n"
        
        # Add encouraging next steps
        response += "**💡 My recommendations:**\n"
        response += "• I'd suggest calling ahead to confirm they're accepting new clients and to ask about any requirements\n"
        response += "• Don't hesitate to mention if you have insurance, Medicaid, or need sliding scale fees\n"
        response += "• If the first place doesn't work out, try the next one - persistence often pays off\n\n"
        
        response += "You're taking all the right steps to get the help you need. Remember, asking for help is a sign of strength, not weakness. I'm here if you need to search for anything else - we're in this together! 🤗"
        
        return response
    
    def chat(self, query: str, category_filter: str = None) -> Dict[str, Any]:
        """Main chat interface - combines search and generation."""
        
        print(f"🔍 Processing query: '{query}'")
        
        # Search for relevant resources
        resources = self.search_resources(query, top_k=5, category_filter=category_filter)
        
        # Generate response
        if self.use_openai and os.getenv('OPENAI_API_KEY'):
            response_text = self.generate_response_openai(query, resources)
        else:
            response_text = self.generate_response_local(query, resources)
        
        # Return structured response
        return {
            'query': query,
            'response': response_text,
            'resources_found': len(resources),
            'top_resources': [
                {
                    'name': r.name,
                    'category': r.category,
                    'phone': r.phone,
                    'address': r.address,
                    'score': r.score
                }
                for r in resources[:3]
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def interactive_mode(self):
        """Run in interactive chat mode."""
        print("🏥 NextStep Healthcare Assistant")
        print("=" * 50)
        print("Ask me about healthcare and social services in Houston!")
        print("Type 'quit' to exit, 'help' for examples")
        print()
        
        while True:
            try:
                query = input("You: ").strip()
                
                if query.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Thank you for using NextStep. Take care!")
                    break
                
                if query.lower() == 'help':
                    print("\n💡 Example questions:")
                    print("- I need mental health counseling")
                    print("- Where can I get free food?")
                    print("- I need help with substance abuse")
                    print("- Emergency shelter for tonight")
                    print("- Dental clinic that accepts Medicaid")
                    print()
                    continue
                
                if not query:
                    continue
                
                # Get response
                result = self.chat(query)
                
                print(f"\nNextStep: {result['response']}")
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Sorry, I encountered an error: {e}")
                print("Please try rephrasing your question.")
    
    def close(self):
        """Close database connections."""
        self.db.close()

def main():
    """Main function for testing the assistant."""
    assistant = NextStepAssistant()
    
    try:
        # Test queries
        test_queries = [
            "I need mental health counseling",
            "Where can I get free food in Houston?",
            "I need help with substance abuse treatment",
            "Emergency shelter for tonight",
            "Free dental clinic"
        ]
        
        print("🤖 Testing NextStep Assistant with Improved Search")
        print("=" * 60)
        
        for query in test_queries:
            print(f"\n🗣️  User: {query}")
            result = assistant.chat(query)
            print(f"🤖 NextStep: {result['response']}")
            print(f"📊 Found {result['resources_found']} resources")
            print("-" * 60)
        
        # Optional: Start interactive mode
        print("\nWould you like to try interactive mode? (y/n)")
        if input().lower().startswith('y'):
            assistant.interactive_mode()
            
    finally:
        assistant.close()

if __name__ == "__main__":
    main() 