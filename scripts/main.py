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
from highlight_manager import HighlightManager
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

def delete_highlight_history(pdf_path: str, batch: int = None):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(script_dir, "tracked_files.db")
    highlight_manager = HighlightManager(db_path)

    # Get the current highlight count
    initial_count = highlight_manager.get_highlight_count(pdf_path, batch)

    # Delete the highlights
    highlight_manager.delete_highlight_history(pdf_path, batch)

    # Get the new highlight count
    final_count = highlight_manager.get_highlight_count(pdf_path, batch)

    if batch:
        print(f"Deleted {initial_count - final_count} highlights from batch {batch} for {pdf_path}")
    else:
        print(f"Deleted {initial_count - final_count} highlights for {pdf_path}")

def main(pdf_path: str, language, batch_size: int, delete_history=False):

    # Load .env file from the root directory of the project
    script_dir = os.path.dirname(os.path.realpath(__file__))
    env_path = os.path.abspath(os.path.join(script_dir, "..", ".env"))
    load_dotenv(dotenv_path=env_path)

    if delete_history:
        delete_highlight_history(pdf_path)
        return

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
    api_key = os.getenv("API_KEY_2")
    provider_name = os.getenv("LLM_PROVIDER")

    # Check if the environment variables are loaded
    if provider_name is None:
        raise ValueError("LLM_PROVIDER environment variable is not set.")
    if api_key is None:
        raise ValueError("API_KEY environment variable is not set.")

    # Create the appropriate LLMProvider instance
    print("Step 3: Loading LLM...")
    llm_provider = get_llm_provider(provider_name, api_key)

    # Step 4: Generate flashcards in batches
    print("Step 4: Generating flashcards in batches...")
    flashcard_generator = FlashcardGenerator(llm_provider)
    output_handler = FlashcardOutputHandler()

    all_flashcards = []

    for i in range(0, len(contexts), batch_size):
        batch = contexts[i:i+batch_size]

        for context in batch:
            highlight_id = context['highlight_id']
            exists = flashcard_generator.highlight_exists(highlight_id)
            if not exists:
                print(f"Generating flashcards for context on page {context['page']}...")
                flashcards = flashcard_generator.generate_flashcards([context], language)
                all_flashcards.extend(flashcards[0])
                flashcard_generator._store_highlight_id(highlight_id, context)
                print(flashcards)

            # Step 5: Create or update Anki deck for this batch
            if all_flashcards:
                print(f"Step 5: Creating/updating Anki deck for batch {i//batch_size + 1}...")
                output_handler.create_anki_deck(
                    flashcards=all_flashcards,
                    deck_name=pdf_path.split("/")[-1],
                    pdf_path=pdf_path,
                )
                print(f"Anki deck updated successfully for batch {i//batch_size + 1}!")
            else:
                print(f"No new highlights found in batch {i//batch_size + 1}. No new flashcards created.")

    print("All batches processed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate flashcards from PDF highlights or delete highlight history."
    )
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    parser.add_argument("--delete-last", type=int, help="Delete the last N highlights")
    parser.add_argument("--delete-history", action="store_true", help="Delete all highlight history for the given PDF")
    parser.add_argument("language", help="Set language of flashcards")
    parser.add_argument("--batch-size", type=int, default=10, help="Number of highlights to process in each batch")
    
    args = parser.parse_args()
    
    if args.delete_last:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        db_path = os.path.join(script_dir, "tracked_files.db")
        highlight_manager = HighlightManager(db_path)
        highlight_manager.delete_last_n_highlights(args.pdf_path, args.delete_last)
    else:
        main(args.pdf_path, args.language, args.batch_size, args.delete_history)
