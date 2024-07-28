import genanki
import logging
import os
import urllib.parse


class FlashcardOutputHandler:
    def create_anki_deck(self, flashcards, deck_name, pdf_path):
        deck = genanki.Deck(2059400110, deck_name)
        model = genanki.Model(
            1607392319,
            "Flashcard with Clickable Source",
            fields=[{"name": "Question"}, {"name": "Answer"}, {"name": "SourceLink"}],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Question}}<br><br><small>{{SourceLink}}</small>",
                    "afmt": "{{FrontSide}}<hr id='answer'>{{Answer}}",
                },
            ],
        )

        valid_flashcards = [fc for fc in flashcards if self._validate_flashcard(fc)]

        for flashcard in valid_flashcards:
            source_link = self._create_source_link(flashcard, pdf_path)
            note = genanki.Note(
                model=model,
                fields=[flashcard["question"], flashcard["answer"], source_link],
            )
            deck.add_note(note)

        if valid_flashcards:
            genanki.Package(deck).write_to_file(f"{deck_name}.apkg")
            logging.info(f"Created Anki deck with {len(valid_flashcards)} flashcards")
        else:
            logging.warning("No valid flashcards to create Anki deck")

    def _validate_flashcard(self, flashcard):
        required_keys = ["question", "answer", "page", "pdf_id", "rect"]
        if all(key in flashcard for key in required_keys):
            return True
        else:
            logging.warning(f"Invalid flashcard: {flashcard}")
            return False

    def _create_source_link(self, flashcard, pdf_path):
        pdf_name = os.path.basename(pdf_path)
        encoded_path = urllib.parse.quote(pdf_path)
        page = flashcard["page"]
        return f'<a href="documentviewer://open?file={encoded_path}&page={page}">{pdf_name} (Page {page})</a>'
