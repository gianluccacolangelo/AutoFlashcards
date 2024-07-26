import fitz  # PyMuPDF
import hashlib


class PDFHandler:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.pdf_id = self._generate_pdf_id()

    def _generate_pdf_id(self):
        # Generate a unique ID for the PDF based on its content
        pdf_content = self.doc.tobytes()
        return hashlib.md5(pdf_content).hexdigest()

    def extract_highlights(self):
        highlights = []
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            for annot in page.annots():
                if annot.type[0] == 8:  # Highlight
                    rect = annot.rect
                    highlighted_text = page.get_textbox(rect)
                    highlight_info = {
                        "text": highlighted_text,
                        "page": page_num + 1,  # Page numbers usually start from 1
                        "pdf_id": self.pdf_id,
                        "rect": rect,  # Store the rectangle coordinates
                    }
                    highlights.append(highlight_info)
        return highlights

    def get_text_by_pages(self, start_page, end_page):
        text = ""
        for page_num in range(start_page, end_page + 1):
            text += self.doc.load_page(page_num).get_text()
        return text
