# test_gemini.py

import os

from google import genai


def main():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents="Say hello in one sentence."
        )

        print("SUCCESS")
        print(response.text)

    except Exception as e:
        print("FAILED")
        print(type(e).__name__)
        print(e)

if __name__ == "__main__":
    main()
