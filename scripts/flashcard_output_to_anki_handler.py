import genanki
import logging
import os
import urllib.parse

class FlashcardOutputHandler:
    def create_anki_deck(self, flashcards, deck_name, pdf_path):
        deck = genanki.Deck(2059400110, deck_name)
        model = genanki.Model(
            1607392319,
            "Flashcard (Apple Minimal Style)",
            fields=[
                {"name": "Question"},
                {"name": "Answer"},
                {"name": "SourceLink"}
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": """
<div class="card-wrapper">
  <div class="card-content">
    <div class="question">{{Question}}</div>
    <div class="source">
      <small>{{SourceLink}}</small>
    </div>
  </div>
</div>
""",
                    "afmt": """
{{FrontSide}}

<hr id="answer" />

<div class="answer">
  {{Answer}}
</div>
"""
                }
            ],
            css="""
/* Body styling */
body {
  background-color: #F8F8F8;
  margin: 0;
  padding: 0;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  color: #333;
}

/* Wrapper around the card */
.card-wrapper {
  max-width: 600px;
  margin: 10% auto;
  padding: 40px;
  background-color: #FFF;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

/* Content container */
.card-content {
  text-align: center;
}

/* Question text */
.question {
  font-size: 1.8rem;
  font-weight: 500;
  margin-bottom: 1rem;
  color: #0A0A0A;
}

/* Source link styling */
.source {
  font-size: 0.875rem;
  color: #999;
}

/* Divider before the answer */
#answer {
  margin: 2rem 0;
  border: none;
  border-top: 1px solid #EEE;
}

/* Answer text */
.answer {
  font-size: 1.3rem;
  line-height: 1.6;
  text-align: left;
  margin: 0 auto;
  max-width: 600px;
}
"""
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
        return f'<a href="documentviewer://open?file={encoded_path}&page={page+1}">{pdf_name} (Page {page+1})</a>'

    def update_source_links(self, old_pdf_path, new_pdf_path):
        old_encoded_path = urllib.parse.quote(old_pdf_path)
        new_encoded_path = urllib.parse.quote(new_pdf_path)
        # Logic to update the source links in Anki notes
