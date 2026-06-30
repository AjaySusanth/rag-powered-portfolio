import os
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not set")

genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-2.5-flash-lite")
response = model.generate_content("Say 'API key is working' and nothing else.")

print(response.text)