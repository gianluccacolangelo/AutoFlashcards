import os
import sqlite3
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMProvider(ABC):
    @abstractmethod
    def __init__(self, api_key: str):
        pass

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        from langchain_openai import OpenAI
        self.llm = OpenAI(api_key=api_key)

    def generate_text(self, prompt: str) -> str:
        return self.llm(prompt)

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        from langchain_community.llms import Anthropic
        self.llm = Anthropic(api_key=api_key)

    def generate_text(self, prompt: str) -> str:
        return self.llm(prompt)

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro-001")

    def generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

class FlashcardGenerator:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        self.db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tracked_files.db")

    @retry(
        stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _generate_text_with_retry(self, prompt: str) -> str:
        try:
            return self.llm_provider.generate_text(prompt)
        except Exception as e:
            logging.error(f"Error generating text: {e}")
            raise

    def generate_flashcards(
        self, contexts: List[Dict[str, str]]
    ) -> List[List[Dict[str, str]]]:
        all_flashcards = []
        for i, context in enumerate(contexts):
            try:
                logging.info(f"Processing context {i+1}/{len(contexts)}")
                prompt = self._create_prompt(context)
                response = self._generate_text_with_retry(prompt)
                flashcards = self._parse_response(response, context)
                all_flashcards.append(flashcards)
                self._store_highlight_id(context['highlight_id'], context)
                time.sleep(1)  # Add a small delay between requests
            except Exception as e:
                logging.error(f"Error processing context {i+1}: {e}")
                continue
        return all_flashcards

    def _create_prompt(self, context: Dict[str, str]) -> str:
        return f"""Generate a flashcard from the following context:

        Context: {context['context']}

        Making special emphasis around the highlight I made: {context['highlight']}

        Please format the flashcard as follows

        Q: [Question]
        A: [Answer]

        And finally, follow these principles in doing flashcards:

        1. They should be atomic, that means, if you have more than two sentences for an answer, you probably should split it out into other flashcards.
        2. They shouldn't "hardcode" knowledge, they have to aim to grasp the fundamentals of the topic, so you can think from first principles.
        3. When you are studying a particular concept, mechanism, or topic, there should be cards that approach the topic from different perspectives, for example, you may study the prove of a theorem with cloze overlapper, but you may have another flashcard with a concrete application of that theorem.

"""

    def _parse_response(
        self, response: str, context: Dict[str, str]
    ) -> List[Dict[str, str]]:
        flashcards = []
        current_flashcard = {}

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("## Flashcard"):
                if current_flashcard:
                    flashcards.append(current_flashcard)
                current_flashcard = {
                    "page": context["page"],
                    "pdf_id": context["pdf_id"],
                    "rect": context["rect"],
                }
            elif line.startswith("**Q:**"):
                current_flashcard["question"] = line[6:].strip()
            elif line.startswith("**A:**"):
                current_flashcard["answer"] = line[6:].strip()

        if current_flashcard:
            flashcards.append(current_flashcard)

        return flashcards

    def highlight_exists(self, highlight_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM highlights WHERE highlight_id = ?", (highlight_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] > 0

    def _store_highlight_id(self, highlight_id: str, context: Dict[str, str]) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO highlights (highlight_id, pdf_id, page, rect, text) VALUES (?, ?, ?, ?, ?)",
            (highlight_id, context["pdf_id"], context["page"], str(context["rect"]), context["highlight"])
        )
        conn.commit()
        conn.close()
