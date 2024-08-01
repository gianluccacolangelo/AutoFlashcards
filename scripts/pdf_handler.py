import fitz  # PyMuPDF
import hashlib

class PDFHandler:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.pdf_id = self._generate_pdf_id()

    def _generate_pdf_id(self):
        # Generate a unique ID for the PDF based on the content of the first few pages
        content = ""
        for page_num in range(min(5, len(self.doc))):  # Use the first 5 pages for ID generation
            page = self.doc.load_page(page_num)
            content += page.get_text()

        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def extract_highlights(self):
        highlights = []
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            for annot in page.annots():
                if annot.type[0] == 8:  # Highlight
                    rect = annot.rect
                    highlighted_text = page.get_textbox(rect).strip()
                    highlight_id = self._generate_highlight_id(page_num, rect, highlighted_text)
                    highlight_info = {
                        "highlight_id": highlight_id,
                        "text": highlighted_text,
                        "page": page_num + 1,  # Page numbers usually start from 1
                        "pdf_id": self.pdf_id,
                        "rect": rect,  # Store the rectangle coordinates
                    }
                    highlights.append(highlight_info)
        return highlights

    def _generate_highlight_id(self, page_num, rect, highlighted_text):
        # Normalize the rectangle coordinates to avoid floating point inconsistencies
        rect_str = f"{rect.x0:.4f}_{rect.y0:.4f}_{rect.x1:.4f}_{rect.y1:.4f}"
        unique_string = f"{self.pdf_id}_{page_num}_{rect_str}_{highlighted_text}"
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

    def get_text_by_pages(self, start_page, end_page):
        text = ""
        for page_num in range(start_page, end_page + 1):
            text += self.doc.load_page(page_num).get_text()
        return text
