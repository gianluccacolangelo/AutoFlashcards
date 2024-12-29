class HighlightContextExtractor:
    def __init__(self, pdf_handler):
        self.pdf_handler = pdf_handler

    def get_contexts(self, highlights, context_range=1):
        contexts = []
        for highlight in highlights:
            start_page = max(
                highlight["page"] - context_range - 1, 0
            )  # Adjust for 0-based index
            end_page = min(
                highlight["page"] + context_range - 1, len(self.pdf_handler.doc) - 1
            )
            context_text = self.pdf_handler.get_text_by_pages(start_page, end_page)
            contexts.append(
                {
                    "highlight": highlight["text"],
                    "highlight_id": highlight["highlight_id"],
                    "context": context_text,
                    "page": highlight["page"],
                    "pdf_id": highlight["pdf_id"],
                    "rect": highlight["rect"],
                    "pdf_path": self.pdf_handler.pdf_path
                }
            )
        return contexts
