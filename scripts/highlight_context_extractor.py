class HighlightContextExtractor:
    def __init__(self, pdf_handler):
        self.pdf_handler = pdf_handler

    def get_contexts(self, highlights, context_range=1):
        contexts = []
        for highlight in highlights:
            start_page = max(highlight["page"] - context_range, 0)
            end_page = min(
                highlight["page"] + context_range, len(self.pdf_handler.doc) - 1
            )
            context_text = self.pdf_handler.get_text_by_pages(start_page, end_page)
            contexts.append({"highlight": highlight["text"], "context": context_text})
        return contexts
