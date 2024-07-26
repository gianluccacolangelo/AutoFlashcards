import genanki


class FlashcardOutputHandler:
    def create_anki_deck(self, flashcards, deck_name):
        deck = genanki.Deck(2059400110, deck_name)
        model = genanki.Model(
            1607392319,
            "Flashcard with Source",
            fields=[{"name": "Question"}, {"name": "Answer"}, {"name": "Source"}],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Question}}<br><br><small>{{Source}}</small>",
                    "afmt": "{{FrontSide}}<hr id='answer'>{{Answer}}",
                },
            ],
        )
        for flashcard in flashcards:
            source = f"PDF ID: {flashcard['pdf_id']}, Page: {flashcard['page']}"
            note = genanki.Note(
                model=model, fields=[flashcard["question"], flashcard["answer"], source]
            )
            deck.add_note(note)
        genanki.Package(deck).write_to_file(f"{deck_name}.apkg")
