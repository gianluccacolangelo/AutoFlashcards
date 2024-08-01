#!/usr/bin/env python3

import os
import argparse
from pdf_handler import PDFHandler
from highlight_context_extractor import HighlightContextExtractor
from flashcard_generator import (
    FlashcardGenerator,
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
)
from flashcard_output_to_anki_handler import FlashcardOutputHandler
from dotenv import load_dotenv


def get_llm_provider(provider_name: str, api_key: str):
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
    }
    if provider_name not in providers:
        raise ValueError(
            f"Unsupported provider: {provider_name}\n\nThe options are: \n{providers}"
        )
    return providers[provider_name](api_key)

def main(pdf_path: str):
    # Load .env file from the root directory of the project
    script_dir = os.path.dirname(os.path.realpath(__file__))
    env_path = os.path.abspath(os.path.join(script_dir, "..", ".env"))
    load_dotenv(dotenv_path=env_path)

    pdf_path = os.path.abspath(pdf_path)

    # Step 1: Extract highlights from the PDF
    print("Step 1: Extracting PDF highlights...")
    pdf_handler = PDFHandler(pdf_path)
    highlights = pdf_handler.extract_highlights()

    # Step 2: Extract contexts from the highlights
    print("Step 2: Extracting contexts from the highlights...")
    context_extractor = HighlightContextExtractor(pdf_handler)
    contexts = context_extractor.get_contexts(highlights)

    # Safely get API key and provider name from .env variables
    api_key = os.getenv("API_KEY")
    provider_name = os.getenv("LLM_PROVIDER")

    # Check if the environment variables are loaded
    if provider_name is None:
        raise ValueError("LLM_PROVIDER environment variable is not set.")
    if api_key is None:
        raise ValueError("API_KEY environment variable is not set.")

    # Create the appropriate LLMProvider instance
    print("Step 3: Loading LLM...")
    llm_provider = get_llm_provider(provider_name, api_key)

    # Step 4: Generate flashcards
    print("Step 4: Generating flashcards...")
    flashcard_generator = FlashcardGenerator(llm_provider)
    all_flashcards = []
    for context in contexts:
        if not flashcard_generator.highlight_exists(context['highlight_id']):
            print(f"Generating flashcards for context on page {context['page']}...")
            flashcards = flashcard_generator.generate_flashcards([context])
            all_flashcards.extend(flashcards[0])

    # Step 5: Create Anki deck
    print("Step 5: Creating Anki deck...")
    output_handler = FlashcardOutputHandler()
    output_handler.create_anki_deck(
        all_flashcards,
        "My Flashcards",
        pdf_path,
    )
    print("Anki deck created successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate flashcards from PDF highlights."
    )
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    parser.add_argument("language", type=str, help="Flashcards language")
    args = parser.parse_args()
    main(args.pdf_path,args.language)
