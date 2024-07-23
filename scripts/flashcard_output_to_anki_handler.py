import genanki


class FlashcardOutputHandler:
    def save_to_txt(self, flashcards, output_path):
        with open(output_path, "w") as f:
            for flashcard in flashcards:
                f.write(f"Q: {flashcard['question']}\nA: {flashcard['answer']}\n\n")

    def create_anki_deck(self, flashcards, deck_name):
        deck = genanki.Deck(2059400110, deck_name)
        model = genanki.Model(
            1607392319,
            "Simple Model",
            fields=[{"name": "Question"}, {"name": "Answer"}],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Question}}",
                    "afmt": "{{Answer}}",
                },
            ],
        )
        for flashcard in flashcards:
            note = genanki.Note(
                model=model, fields=[flashcard["question"], flashcard["answer"]]
            )
            deck.add_note(note)
        genanki.Package(deck).write_to_file(f"{deck_name}.apkg")
