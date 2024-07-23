from langchain import OpenAI


class FlashcardGenerator:
    def __init__(self, llm_api_key):
        self.llm = OpenAI(api_key=llm_api_key)

    def generate_flashcards(self, contexts):
        flashcards = []
        for context in contexts:
            prompt = f"Generate a flashcard from the following context:\n\n{context['context']}\n\nHighlight: {context['highlight']}\n"
            response = self.llm(prompt)
            flashcards.append(response)
        return flashcards
