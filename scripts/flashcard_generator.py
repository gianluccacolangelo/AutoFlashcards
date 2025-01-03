import os
import sqlite3
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image, ImageOps
import hashlib
from image_handler import PDFImageHandler

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
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_text(self, prompt: str) -> str:
        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0,
            system="You are an AI assistant designed to generate flashcards based on given contexts.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return message.content[0].text

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp")

    def generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

class FlashcardGenerator:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        self.db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tracked_files.db")

    @retry(
        stop=stop_after_attempt(20), wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    def _generate_text_with_retry(self, prompt: str) -> str:
        try:
            return self.llm_provider.generate_text(prompt)
        except Exception as e:
            logging.error(f"Error generating text: {e}")
            raise

    def generate_flashcards(
        self, contexts: List[Dict[str, str]],
        language: str
    ) -> List[List[Dict[str, str]]]:
        # Add image handler
        image_handler = PDFImageHandler()
        
        all_flashcards = []
        for i, context in enumerate(contexts):
            try:
                logging.info(f"Processing context {i+1}/{len(contexts)}")
                
                # Generate context image
                context_image = image_handler.create_context_image(
                    context['pdf_path'],  # Make sure this is passed in the context
                    context['page'],
                    context['pdf_id']
                )
                
                prompt = self._create_prompt(context, language)
                response = self._generate_text_with_retry(prompt)
                print(response)
                flashcards = self._parse_response(response, context)
                
                # Add image to each flashcard
                for flashcard in flashcards:
                    flashcard['context_image'] = context_image
                    
                all_flashcards.append(flashcards)
                self._store_highlight_id(context['highlight_id'], context)
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error processing context {i+1}: {e}")
                continue
        return all_flashcards

    def _create_prompt(self, context: Dict[str, str],language: str) -> str:
        return f"""Generate a flashcard in {language} from the following context:

        Context: {context['context']}

        Making special emphasis around the highlight I made: {context['highlight']}

        Please format the flashcard **exactly** as follows

        Q: questionhere
        A: answerhere

        And finally, follow these principles in doing flashcards:

        1. They should be atomic, that means, if you have more than two sentences for an answer, you probably should split it out into other flashcards.
        2. They shouldn't "hardcode" knowledge, they have to aim to grasp the fundamentals of the topic, so you can think from first principles.
        3. When you are studying a particular concept, mechanism, or topic, there should be cards that approach the topic from different perspectives, for example, you may study the prove of a theorem, but you may have another flashcard with a concrete application of that theorem.
        4. ALWAYS get sure that the answer is being asked. For example, this is what you shouldn't do: Q: "can we always solve Ax=b for every b?" A: "No. It depends on whether the columns of A are independent and span the space.". Because "on which depends" **was never asked**. For having that answer, you should rather put in the question: "On what _depends_ if we can solve Ax=b for every b?".
        5. When its needed, you can give one to three sentences of context to introduce the question. The answer should always remain atomic, but sometimes its better to situate the question in context.

"""

    def _parse_response(self, response: str, context: Dict[str, str]) -> List[Dict[str, str]]:
        flashcards = []
        lines = response.split('\n')
        current_flashcard = {}

        for line in lines:
            line = line.strip()

            if line.startswith('Q:') or line.startswith('**Q:**'):
                if current_flashcard:
                    flashcards.append(current_flashcard)
                current_flashcard = {
                    "question": line[6:].strip() if line.startswith('**Q:**') else line[2:].strip(),
                    "page": context["page"],
                    "pdf_id": context["pdf_id"],
                    "rect": context["rect"],
                    "pdf_path": context.get("pdf_path", "")  # Add pdf_path to the flashcard
                }
            elif line.startswith('A:') or line.startswith('**A:**'):
                current_flashcard["answer"] = line[6:].strip() if line.startswith('**A:**') else line[2:].strip()

        # Add the last flashcard if it exists
        if current_flashcard and "answer" in current_flashcard:
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
