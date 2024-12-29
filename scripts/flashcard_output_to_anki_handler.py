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
            "Simple Image Card",  # Changed to match the Anki note type
            fields=[
                {"name": "Front"},  # Question
                {"name": "Back"},   # Answer
                {"name": "Image"}   # Context image
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": """
<div class="front">{{Front}}</div>
""",
                    "afmt": """
{{FrontSide}}
<hr>
<div class="back">{{Back}}</div>

<button onclick="toggleImage()" class="toggle-btn" id="toggleBtn">View document</button>

<div class="image-container" id="imageContainer" style="display: none;">
    <img src="{{Image}}" 
         style="
           width:100% !important;
           max-width:98.7% !important;
           max-height:100% !important;
           display:block !important;
           margin:10 10 10 10 !important;
         "
         onload="centerImage()">
</div>
<script>
function centerImage() {
    const container = document.getElementById('imageContainer');
    const img = container.querySelector('img');
    if (img.height > container.clientHeight) {
        container.scrollTop = (container.scrollHeight - container.clientHeight) / 2;
    }
}

function toggleImage() {
    const container = document.getElementById('imageContainer');
    const btn = document.getElementById('toggleBtn');
    if (container.style.display === 'none') {
        container.style.display = 'block';
        btn.textContent = 'Hide document';
        setTimeout(centerImage, 50);
    } else {
        container.style.display = 'none';
        btn.textContent = 'View document';
    }
}
</script>
""",
                }
            ],
            css="""
.card {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
    padding: 20px;
}

.front {
    font-size: 24px;
    margin-bottom: 20px;
}

.back {
    margin: 20px 0;
}

.toggle-btn {
    background-color: transparent;
    border: none;
    color: #007AFF;
    padding: 8px 16px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 15px;
    font-weight: 500;
    margin: 4px 2px;
    cursor: pointer;
    border-radius: 6px;
    transition: all 0.2s ease;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.toggle-btn:hover {
    background-color: rgba(0, 122, 255, 0.1);
}

.toggle-btn:active {
    background-color: rgba(0, 122, 255, 0.2);
}

.image-container {
    max-height: 300px;
    overflow-y: auto;
    overflow-x: hidden;
    margin: 10px auto;
    border-radius: 8px;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}
"""
        )

        valid_flashcards = [fc for fc in flashcards if self._validate_flashcard(fc)]

        for flashcard in valid_flashcards:
            note = genanki.Note(
                model=model,
                fields=[
                    flashcard["question"],                    # Front
                    flashcard["answer"],                      # Back
                    flashcard["context_image"]                # Image
                ]
            )
            deck.add_note(note)

            # Add image to media files
            if "context_image" in flashcard:
                self.media_files.append((
                    os.path.join("pdf_images", flashcard["context_image"]),
                    flashcard["context_image"]
                ))

        if valid_flashcards:
            # Create a package with the deck and media files
            package = genanki.Package(deck)
            package.media_files = [path for path, _ in self.media_files]
            output_file = f"{deck_name}.apkg"
            package.write_to_file(output_file)

            # Clean up temporary files
            for temp_file, _ in self.media_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

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
