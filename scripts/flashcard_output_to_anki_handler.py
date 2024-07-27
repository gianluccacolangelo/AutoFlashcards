import genanki
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
        for flashcard in flashcards:
            source_link = self._create_source_link(flashcard, pdf_path)
            note = genanki.Note(
                model=model,
                fields=[flashcard["question"], flashcard["answer"], source_link],
            )
            deck.add_note(note)
        genanki.Package(deck).write_to_file(f"{deck_name}.apkg")

    def _create_source_link(self, flashcard, pdf_path):
        pdf_name = os.path.basename(pdf_path)
        encoded_path = urllib.parse.quote(pdf_path)
        page = flashcard["page"]
        return f'<a href="documentviewer://open?file={encoded_path}&page={page}">{pdf_name} (Page {page})</a>'
