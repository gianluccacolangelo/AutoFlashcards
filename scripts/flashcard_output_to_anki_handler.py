import genanki
import logging
import os
import urllib.parse
import shutil
import fitz  # PyMuPDF
import tempfile
from pdf_handler import PDFHandler

class FlashcardOutputHandler:
    def __init__(self):
        self.media_files = []

    def _compress_pdf(self, input_pdf_path):
        """Compress PDF and return the path to the compressed file"""
        doc = fitz.open(input_pdf_path)
        
        # Create a temporary file for the compressed PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            compressed_path = tmp_file.name
        
        # Save with compression
        doc.save(compressed_path, 
                garbage=4,  # Maximum garbage collection
                deflate=True,  # Use deflate compression
                clean=True,  # Clean unused elements
                linear=True)  # Optimize for web viewing
        
        doc.close()
        return compressed_path

    def _prepare_pdf_for_anki(self, pdf_path):
        """Prepare PDF for Anki by compressing and generating a unique filename"""
        # Generate a unique filename based on the PDF content
        pdf_handler = PDFHandler(pdf_path)
        unique_name = f"_source_{pdf_handler.pdf_id[:8]}.pdf"  # Prefix with _source_ to ensure Anki treats it as media
        
        # Compress the PDF
        compressed_path = self._compress_pdf(pdf_path)
        
        # Add to media files list with the correct name mapping
        self.media_files.append((compressed_path, unique_name))
        
        return unique_name

    def create_anki_deck(self, flashcards, deck_name, pdf_path):
        # Prepare PDF for Anki
        anki_pdf_name = self._prepare_pdf_for_anki(pdf_path)
        original_pdf_name = os.path.basename(pdf_path)
        
        deck = genanki.Deck(2059400110, deck_name)
        model = genanki.Model(
            1607392319,
            "Flashcard (Apple Minimal Style)",
            fields=[
                {"name": "Question"},
                {"name": "Answer"},
                {"name": "SourceLink"},
                {"name": "PDFFile"},
                {"name": "PageNumber"}
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

<div class="pdf-section">
  <div class="pdf-info">Source: {{PDFFile}} (Page {{PageNumber}})</div>
  <div class="pdf-viewer">
    <iframe src="{{PDFFile}}#page={{PageNumber}}" type="application/pdf" width="100%" height="600px" class="pdf-frame"></iframe>
  </div>
</div>
""",
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
  max-width: 800px;  /* Increased for better PDF viewing */
  margin: 5% auto;
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
  max-width: 800px;  /* Increased for better readability */
}

/* PDF section styling */
.pdf-section {
  margin-top: 2rem;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.pdf-info {
  text-align: center;
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 1rem;
}

.pdf-viewer {
  width: 100%;
  margin: 0 auto;
  background: #f5f5f5;
  border-radius: 4px;
  overflow: hidden;
}

.pdf-frame {
  border: none;
  display: block;
  margin: 0 auto;
  background: white;
}

/* Make the PDF viewer responsive */
@media (max-width: 768px) {
  .card-wrapper {
    padding: 20px;
    margin: 2% auto;
  }
  
  .pdf-frame {
    height: 400px;  /* Smaller height on mobile */
  }
}
"""
        )

        valid_flashcards = [fc for fc in flashcards if self._validate_flashcard(fc)]

        for flashcard in valid_flashcards:
            source_link = self._create_source_link(flashcard, original_pdf_name)
            note = genanki.Note(
                model=model,
                fields=[
                    flashcard["question"],
                    flashcard["answer"],
                    source_link,
                    anki_pdf_name,
                    str(flashcard["page"] + 1)
                ],
            )
            deck.add_note(note)

        if valid_flashcards:
            # Create a package with the deck and media files
            package = genanki.Package(deck)
            
            # Add the media files with their correct names
            media_files_with_names = []
            for temp_path, dest_name in self.media_files:
                new_path = os.path.join(os.path.dirname(temp_path), dest_name)
                shutil.copy2(temp_path, new_path)
                media_files_with_names.append(new_path)
            
            package.media_files = media_files_with_names
            
            # Write the package to file
            output_file = f"{deck_name}.apkg"
            package.write_to_file(output_file)
            
            # Clean up temporary files
            for temp_file, _ in self.media_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            for media_file in media_files_with_names:
                if os.path.exists(media_file):
                    os.remove(media_file)
            
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

    def _create_source_link(self, flashcard, original_pdf_name):
        """Create a source link that shows the PDF source information"""
        page = flashcard["page"]
        return f"{original_pdf_name} (Page {page+1})"

    def update_source_links(self, old_pdf_path, new_pdf_path):
        old_encoded_path = urllib.parse.quote(old_pdf_path)
        new_encoded_path = urllib.parse.quote(new_pdf_path)
        # Logic to update the source links in Anki notes
