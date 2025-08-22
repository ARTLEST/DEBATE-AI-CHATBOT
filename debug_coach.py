#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import openai
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json

# Load environment variables
load_dotenv()

# AI Configuration
class DebateAI:
    def __init__(self):
        # Configure your AI model here
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        self.model_name = "gpt-3.5-turbo"
        self.serpapi_key = os.environ.get('SERPAPI_KEY')  # For web search

    def search_web_facts(self, query, num_results=3):
        """Search the web for factual information to support arguments"""
        try:
            if self.serpapi_key:
                # Using SerpAPI for reliable search results
                url = "https://serpapi.com/search"
                params = {
                    "engine": "google",
                    "q": query,
                    "api_key": self.serpapi_key,
                    "num": num_results
                }
                response = requests.get(url, params=params)
                results = response.json()

                facts = []
                if "organic_results" in results:
                    for result in results["organic_results"][:num_results]:
                        facts.append({
                            "title": result.get("title", ""),
                            "snippet": result.get("snippet", ""),
                            "source": result.get("link", "")
                        })
                return facts
            else:
                # Fallback: Basic web scraping (less reliable)
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                response = requests.get(search_url, headers=headers, timeout=5)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    snippets = soup.find_all('span', class_='aCOpRe')
                    facts = []
                    for snippet in snippets[:num_results]:
                        if snippet.text:
                            facts.append({
                                "title": "Search Result",
                                "snippet": snippet.text,
                                "source": "Google Search"
                            })
                    return facts

        except Exception as e:
            print(f"Web search error: {e}")

        return []

    def analyze_debate_message(self, topic, user_position, user_message, message_context, message_count):
        """Analyze user's debate message in context and provide detailed feedback with perfect answer"""

        # Search for relevant facts to support analysis
        search_query = f"{topic} evidence statistics facts research"
        web_facts = self.search_web_facts(search_query)

        fact_context = ""
        if web_facts:
            fact_context = "Recent web research findings:\n"
            for fact in web_facts:
                fact_context += f"- {fact['snippet']}\n"

        prompt = f"""
        You are an expert debate coach analyzing a debate message. Here's the context:

        Debate Topic: {topic}
        User's Position: {user_position}
        Message #{message_count}
        User's Message: {user_message}
        Previous Context: {message_context[-3:] if message_context else 'This is the opening statement'}

        {fact_context}

        Analyze this message and provide detailed feedback in the following JSON format:
        {{
            "score": [1-10 score based on argument quality, evidence, structure, persuasiveness],
            "strengths": ["specific positive elements in this argument"],
            "improvements": ["specific actionable improvements"],
            "counterarguments": ["actual counterarguments opponents would make"],
            "evidence": ["specific types of evidence that would strengthen this exact argument"],
            "overall_feedback": "comprehensive coaching feedback paragraph",
            "perfect_answer": "A complete, well-structured argument that demonstrates what they should have said - include specific facts, evidence, and persuasive language. Make this a full argument, not a description."
        }}

        For the perfect_answer: Write an actual debate argument that addresses the same point but with superior structure, evidence, and persuasiveness. Include specific facts where possible.
        """

        try:
            if self.client:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1500
                )
                result = json.loads(response.choices[0].message.content)

                # Enhance perfect answer with web facts if available
                if web_facts and 'perfect_answer' in result:
                    enhanced_answer = result['perfect_answer']
                    relevant_fact = web_facts[0]['snippet'] if web_facts else ""
                    if relevant_fact and len(relevant_fact) > 20:
                        enhanced_answer += f" According to recent research, {relevant_fact}"
                    result['perfect_answer'] = enhanced_answer

                return result
            else:
                # Mock response for testing without API key
                return {
                    "score": 7,
                    "strengths": ["Clear position", "Logical structure"],
                    "improvements": ["Add specific evidence", "Address counterarguments"],
                    "counterarguments": ["Opponents might argue about implementation costs"],
                    "evidence": ["Statistical data", "Expert testimonials"],
                    "overall_feedback": "Good start, but needs more evidence and depth.",
                    "perfect_answer": "A stronger argument would include specific statistics and expert opinions to support your position."
                }

        except Exception as e:
            return {"error": f"AI processing error: {str(e)}"}

def test_ai_functionality():
    print("Testing AI Debate Coach functionality...\n")

    # Initialize AI
    debate_ai = DebateAI()

    # Test 1: Basic AI initialization
    print("1. Testing AI initialization...")
    print(f"   OpenAI client available: {debate_ai.client is not None}")
    print(f"   API key configured: {'Yes' if debate_ai.api_key else 'No'}")
    print(f"   Model: {debate_ai.model_name}")

    # Test 2: Web search functionality
    print("\n2. Testing web search...")
    facts = debate_ai.search_web_facts("climate change evidence", 2)
    print(f"   Found {len(facts)} web facts")
    for i, fact in enumerate(facts[:2]):
        print(f"   Fact {i+1}: {fact.get('snippet', 'No snippet')[:100]}...")

    # Test 3: Debate analysis
    print("\n3. Testing debate analysis...")
    topic = "Social media should be regulated"
    position = "for"
    argument = "Social media platforms have too much power and spread misinformation, so they need government oversight."

    feedback = debate_ai.analyze_debate_message(topic, position, argument, [], 1)
    print(f"   Analysis completed: {type(feedback)}")
    print(f"   Score: {feedback.get('score', 'N/A')}/10")
    print(f"   Strengths: {len(feedback.get('strengths', []))}")
    print(f"   Improvements: {len(feedback.get('improvements', []))}")
    print(f"   Perfect answer preview: {feedback.get('perfect_answer', 'None')[:100]}...")

    # Show the full feedback
    print(f"\n   Full feedback:")
    for key, value in feedback.items():
        if key == 'perfect_answer':
            print(f"   {key}: {value[:200]}...")
        else:
            print(f"   {key}: {value}")

    print("\n✅ All tests completed!")
    return True

if __name__ == "__main__":
    test_ai_functionality()
