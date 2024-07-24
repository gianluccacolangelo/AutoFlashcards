import os
from pdf_handler import PDFHandler
from highlight_context_extractor import HighlightContextExtractor
from flashcard_generator import FlashcardGenerator
from flashcard_output_to_anki_handler import FlashcardOutputHandler
from dotenv import dotenv_values



def main():
    pdf_path = "sample_01.pdf"
    pdf_handler = PDFHandler(pdf_path)
    highlights = pdf_handler.extract_highlights()

    context_extractor = HighlightContextExtractor(pdf_handler)
    contexts = context_extractor.get_contexts(highlights)

    api_key = dotenv_values("../.env")["API_KEY"] # Safely store key in .env
    flashcard_generator = FlashcardGenerator(api_key)
    flashcards = flashcard_generator.generate_flashcards(contexts)

    output_handler = FlashcardOutputHandler()
    output_handler.save_to_txt(flashcards, "output_flashcards.txt")
    output_handler.create_anki_deck(flashcards, "My Flashcards")


if __name__ == "__main__":
    main()
