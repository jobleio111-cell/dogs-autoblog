"""
AI Writer Module
Gemini API se SEO-optimized English blog post generate karta hai
Finance & Money Making niche ke liye
"""

import requests
import json
import re
from datetime import datetime


class AIWriter:
    def __init__(self, config: dict):
        self.config = config
        self.api_key = config.get("gemini_api_key", config.get("groq_api_key", ""))
        self.is_groq = self.api_key.startswith("gsk_")
        self.model = "llama-3.3-70b-versatile" if self.is_groq else self._get_best_model()
        self.min_words = config.get("min_word_count", 1000)

    def _get_best_model(self) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get("models", [])
            names = [m["name"].split("/")[-1] for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
            for target in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]:
                if target in names:
                    return target
            if names:
                return names[0]
        return "gemini-2.5-flash"

    def _generate_text(self, prompt: str) -> str:
        """Helper to generate text using REST API with rate limit handling"""
        import time
        
        if self.is_groq:
            print("   🤖 Groq (Llama 3) Engine Detected! Running lightning fast...")
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }
            
            for attempt in range(3):
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    time.sleep(2)
                    return response.json()['choices'][0]['message']['content']
                elif response.status_code == 429:
                    print(f"   ⏳ Groq Rate limit hit! Waiting 30s before retry {attempt+1}/3...")
                    time.sleep(30)
                else:
                    raise Exception(f"Groq API Error {response.status_code}: {response.text}")
            raise Exception("Groq API Error: Max retries exceeded.")
            
        # --- Google Gemini Logic ---
        
        # Google Free Tier limits to 5 requests per minute.
        # Sleeping 15 seconds ensures we only make 4 requests per minute, completely avoiding 429 errors.
        print("   ⏳ Rate limit se bachne ke liye 15s wait kar raha hoon...")
        time.sleep(15)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                time.sleep(2)  # Small delay to be safe
                return response.json()['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                print(f"   ⚠️ 429 Error Details: {response.text[:200]}")
                print(f"   ⏳ Rate limit hit! Google ne block kiya, 60 seconds ka wait kar raha hoon for retry {attempt + 1}/{max_retries}...")
                
                # If using 2.5-flash, the daily quota (50) might be exhausted. Switch to 1.5-flash (1500 limit).
                if "gemini-2.5-flash" in url:
                    print("   🔄 Switching to gemini-1.5-flash because 2.5-flash daily quota might be exhausted...")
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                
                time.sleep(60)
            elif response.status_code in [500, 503]:
                print(f"   ⚠️ Server Overloaded (503)! Switching to gemini-1.5-flash for retry {attempt + 1}/{max_retries}...")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
                time.sleep(5)
            else:
                raise Exception(f"Gemini API Error {response.status_code}: {response.text}")
                
        raise Exception("Gemini API Error: Max retries exceeded due to rate limits.")

    def generate_full_post(self, topic: str) -> dict:
        """
        Ek topic par puri blog post generate karo in a single API call to avoid rate limits
        """
        print(f"\n✍️ AI Writer: '{topic}' par ek hi request mein puri post JSON format mein likh raha hoon...")

        prompt = f"""
        You are an expert SEO blog writer. Write a comprehensive, highly engaging, and professional blog post about '{topic}' for an online female fashion and latest trends blog.
        The post MUST be detailed and informative. Use HTML formatting (<h2>, <h3>, <ul>, <li>, <strong>).
        IMPORTANT: DO NOT include any <img> tags, image placeholders, or markdown images in the html_content. Images will be handled separately.
        
        You MUST return ONLY a valid JSON object with the following exact keys:
        - "seo_title": A highly engaging, clickbait but professional SEO title.
        - "keywords": An array of exactly 10 SEO keywords/phrases.
        - "html_content": The main HTML body content of the blog post (highly informative, at least {self.min_words} words).
        - "meta_description": A compelling SEO meta description (max 160 characters).
        - "pinterest_tags": An array of 20 Pinterest hashtags starting with #.
        - "pin_description": A plain text, natural human-readable Pinterest description (max 450 chars). No HTML tags, no meta tags, no comments. Must include the main keyword.
        - "blogger_labels": An array of 5 highly relevant categories/tags.
        
        Return ONLY valid JSON. Do not include markdown code blocks like ```json.
        """

        json_str = self._generate_text(prompt)

        # Clean up JSON if AI returned markdown code blocks
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]

        try:
            data = json.loads(json_str.strip(), strict=False)
        except Exception as e:
            print(f"   ❌ JSON Parsing Error: {e}")
            raise Exception("Failed to parse AI JSON response")

        return {
            "topic": topic,
            "seo_title": data.get("seo_title", topic),
            "html_content": data.get("html_content", "<p>Content generation failed.</p>"),
            "meta_description": data.get("meta_description", ""),
            "focus_keywords": data.get("keywords", []),
            "pinterest_tags": data.get("pinterest_tags", []),
            "pin_description": data.get("pin_description", ""),
            "blogger_labels": data.get("blogger_labels", []),
            "generated_at": datetime.now().isoformat(),
            "word_count": len(data.get("html_content", "").split())
        }

if __name__ == "__main__":
    # Test karo
    with open("config.json") as f:
        config = json.load(f)

    writer = AIWriter(config)
    result = writer.generate_full_post("How to Build Passive Income with Dividend Stocks")

    print("\n=== GENERATED POST ===")
    print(f"Title: {result['seo_title']}")
    print(f"Meta: {result['meta_description']}")
    print(f"Keywords: {result['focus_keywords']}")
    print(f"Pinterest Tags: {result['pinterest_tags'][:5]}")
    print(f"Word Count: {result['word_count']}")
