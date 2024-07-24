import unittest
import sys
import os

# Add the parent directory (AutoFlashcards) to the sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.pdf_handler import PDFHandler


class TestPDFHandler(unittest.TestCase):

    def setUp(self):
        self.pdf_handler = PDFHandler("../sample_01.pdf")

    def test_extract_highlights(self):
        highlights = self.pdf_handler.extract_highlights()
        print(f"Test Extract Highlights: {highlights}")  # Print statement for debugging
        self.assertIsInstance(highlights, list)
        for highlight in highlights:
            self.assertIn("text", highlight)
            self.assertIn("page", highlight)

    def test_get_text_by_pages(self):
        text = self.pdf_handler.get_text_by_pages(0, 2)
        print(f"Test Get Text By Pages: {text}")  # Print statement for debugging
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)


if __name__ == "__main__":
    unittest.main()
