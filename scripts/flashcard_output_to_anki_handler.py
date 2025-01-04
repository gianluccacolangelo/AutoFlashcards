import genanki
import logging
import os
import urllib.parse
import shutil
import fitz  # PyMuPDF
import tempfile
from pdf_handler import PDFHandler
import json
import sqlite3
from pathlib import Path
import re

class FlashcardOutputHandler:
    def __init__(self):
        self.media_files = set()

    def _prepare_context_image(self, original_filename):
        """Prepare image filename for Anki by ensuring it follows Anki's naming conventions"""
        # Remove any problematic characters and ensure it starts with underscore
        # Anki requires media files to start with underscore if they're references in HTML
        safe_name = "_" + re.sub(r'[^\w\s-]', '', original_filename)
        return safe_name

    def create_anki_deck(self, flashcards, deck_name, pdf_path):
        deck = genanki.Deck(2059400110, deck_name)
        model = genanki.Model(
            1607392319,
            "Simple Image Card",
            fields=[
                {"name": "Front"},
                {"name": "Back"},
                {"name": "Image"}
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
            if "context_image" in flashcard:
                source_path = os.path.join("pdf_images", flashcard["context_image"])
                if os.path.exists(source_path):
                    # Prepare a safe filename for Anki
                    anki_filename = self._prepare_context_image(flashcard["context_image"])
                    
                    # Add to set instead of list to prevent duplicates
                    self.media_files.add((source_path, anki_filename))
                    
                    note = genanki.Note(
                        model=model,
                        fields=[
                            flashcard["question"],
                            flashcard["answer"],
                            anki_filename
                        ]
                    )
                    deck.add_note(note)

        if valid_flashcards:
            package = genanki.Package(deck)
            
            # Convert set to list of unique media files
            media_files = []
            for source_path, anki_filename in self.media_files:
                if os.path.exists(source_path):
                    temp_path = os.path.join(os.path.dirname(source_path), anki_filename)
                    shutil.copy2(source_path, temp_path)
                    media_files.append(temp_path)
                    logging.info(f"Added media file: {temp_path}")
            
            package.media_files = media_files
            
            # Write the package
            output_file = f"{deck_name}.apkg"
            package.write_to_file(output_file)
            
            # Clean up temporary files
            for temp_path in media_files:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
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
