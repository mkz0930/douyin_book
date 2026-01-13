from openai import OpenAI
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import API_KEY, BASE_URL, MODEL_NAME, SCRIPT_GENERATION_PROMPT, IMAGE_PROMPT_GENERATION_PROMPT, SCRIPT_GENERATION_FROM_SUMMARY_PROMPT, BOOK_NAME_EXTRACTION_PROMPT

class LLMClient:
    def __init__(self):
        if not API_KEY:
            raise ValueError("API_KEY not found in environment variables. Please check your .env file.")
        
        self.client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL
        )

    def generate_script(self, book_content):
        """
        Generates a Douyin script based on the book content.
        """
        prompt = SCRIPT_GENERATION_PROMPT.format(book_content=book_content)
        return self._call_llm(prompt)

    def generate_script_from_summary(self, book_name, summary):
        """
        Generates a script based on search summary (when full text is missing).
        """
        prompt = SCRIPT_GENERATION_FROM_SUMMARY_PROMPT.format(book_name=book_name, summary=summary)
        return self._call_llm(prompt)

    def generate_image_prompt(self, script_segment):
        """
        Generates an image prompt based on a script segment.
        """
        prompt = IMAGE_PROMPT_GENERATION_PROMPT.format(script_segment=script_segment)
        return self._call_llm(prompt)

    def extract_book_name(self, content):
        """
        Extracts or infers the book name from the content.
        """
        # Truncate content if it's too long to avoid token limits, just for name extraction
        truncated_content = content[:2000]
        prompt = BOOK_NAME_EXTRACTION_PROMPT.format(content=truncated_content)
        book_name = self._call_llm(prompt)
        if book_name:
            return book_name.strip()
        return None

    def _call_llm(self, prompt):
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "你是一位专业的助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None

if __name__ == "__main__":
    # Test stub
    client = LLMClient()
    print("LLM Client initialized successfully.")
