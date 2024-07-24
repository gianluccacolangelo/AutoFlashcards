from abc import ABC, abstractmethod
from typing import List, Dict


class LLMProvider(ABC):
    @abstractmethod
    def __init__(self, api_key: str):
        pass

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        from langchain_community.llms import OpenAI

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
        self.model = genai.GenerativeModel("gemini-pro")

    def generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text


class FlashcardGenerator:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    def generate_flashcards(
        self, contexts: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        flashcards = []
        for context in contexts:
            prompt = self._create_prompt(context)
            response = self.llm_provider.generate_text(prompt)
            flashcard = self._parse_response(response)
            flashcards.append(flashcard)
        return flashcards

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

    def _parse_response(self, response: str) -> Dict[str, str]:
        lines = response.strip().split("\n")
        question = lines[0][3:].strip() if lines[0].startswith("Q:") else ""
        answer = (
            lines[1][3:].strip() if len(lines) > 1 and lines[1].startswith("A:") else ""
        )
        return {"question": question, "answer": answer}
