import fitz  # PyMuPDF


class PDFHandler:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def extract_highlights(self):
        highlights = []
        for page_num in range(len(self.doc)):
            page = self.doc.load_page(page_num)
            for annot in page.annots():
                if annot.type[0] == 8:  # Highlight
                    highlight_info = {"text": annot.info["content"], "page": page_num}
                    highlights.append(highlight_info)
        return highlights

    def get_text_by_pages(self, start_page, end_page):
        text = ""
        for page_num in range(start_page, end_page + 1):
            text += self.doc.load_page(page_num).get_text()
        return text
