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

class FlashcardOutputHandler:
    def __init__(self):
        self.media_files = []
        self.media_path = self._get_media_path()
        if self.media_path:
            logging.info(f"Using Anki media path: {self.media_path}")
        else:
            logging.warning("Could not find Anki media collection path")

    def _get_media_path(self):
        """Get the Anki media collection path based on context (add-on vs standalone)"""
        try:
            # First try: Running as Anki add-on
            from aqt import mw
            if mw and mw.pm:
                addon_media_path = os.path.join(mw.pm.profileFolder(), "collection.media")
                if os.path.exists(addon_media_path):
                    return addon_media_path
        except ImportError:
            pass

        # Second try: Running as standalone, check common Anki locations
        possible_paths = []
        
        # Windows path
        if os.name == 'nt':
            possible_paths.append(Path.home() / "AppData/Roaming/Anki2")
        
        # Linux paths
        elif os.name == 'posix':
            possible_paths.extend([
                Path.home() / ".local/share/Anki2",
                Path.home() / "Anki2"  # Legacy location
            ])
            
        # MacOS paths
        if os.name == 'posix' and os.path.exists(str(Path.home() / "Library")):
            possible_paths.append(Path.home() / "Library/Application Support/Anki2")

        # Try to find the active profile
        for base_path in possible_paths:
            if not base_path.exists():
                continue

            # Try to get active profile from prefs.db
            prefs_db = base_path / "prefs.db"
            if prefs_db.exists():
                try:
                    conn = sqlite3.connect(str(prefs_db))
                    cursor = conn.cursor()
                    cursor.execute("SELECT value FROM prefs WHERE key='activeProfile'")
                    result = cursor.fetchone()
                    conn.close()

                    if result and result[0]:
                        profile_name = result[0]
                        media_path = base_path / profile_name / "collection.media"
                        if media_path.exists():
                            return str(media_path)
                except sqlite3.Error as e:
                    logging.debug(f"Error reading prefs.db: {e}")
                    continue

            # Fallback: Look for profile folders directly
            for profile_dir in base_path.iterdir():
                if profile_dir.is_dir():
                    media_path = profile_dir / "collection.media"
                    if media_path.exists():
                        return str(media_path)

        return None

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
        if not self.media_path:
            logging.warning("Could not find Anki media collection path. Images will only be included in the package.")
        else:
            logging.info(f"Using Anki media path: {self.media_path}")

        # Prepare PDF for Anki
        anki_pdf_name = self._prepare_pdf_for_anki(pdf_path)
        original_pdf_name = os.path.basename(pdf_path)

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
            # Copy image to Anki media collection if possible
            if "context_image" in flashcard and self.media_path:
                source_path = os.path.join("pdf_images", flashcard["context_image"])
                dest_path = os.path.join(self.media_path, flashcard["context_image"])
                if os.path.exists(source_path):
                    try:
                        shutil.copy2(source_path, dest_path)
                        logging.info(f"Copied image to Anki media: {flashcard['context_image']}")
                    except Exception as e:
                        logging.error(f"Failed to copy image to Anki media: {e}")

            note = genanki.Note(
                model=model,
                fields=[
                    flashcard["question"],
                    flashcard["answer"],
                    flashcard["context_image"]
                ]
            )
            deck.add_note(note)

            # Keep track of media files for the package
            if "context_image" in flashcard:
                self.media_files.append((
                    os.path.join("pdf_images", flashcard["context_image"]),
                    flashcard["context_image"]
                ))

        if valid_flashcards:
            package = genanki.Package(deck)
            package.media_files = [path for path, _ in self.media_files]
            output_file = f"{deck_name}.apkg"
            package.write_to_file(output_file)
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
