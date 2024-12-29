from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image, ImageOps
import os
import hashlib

class PDFImageHandler:
    def __init__(self, output_dir="pdf_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_context_image(self, pdf_path, page_number, pdf_id, zoom_factor=2, grayscale=False):
        """Creates a context image for a highlight and returns the image filename"""
        # Generate unique filename based on PDF ID and page
        image_id = hashlib.md5(f"{pdf_id}_{page_number}".encode()).hexdigest()[:8]
        output_file = f"context_{image_id}.jpg"
        output_path = os.path.join(self.output_dir, output_file)

        # Skip if image already exists
        if os.path.exists(output_path):
            return output_file

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        # Calculate the range of pages to extract
        start_page = max(page_number - 3, 1)
        end_page = min(page_number + 3, total_pages)

        # Convert specified pages to images
        images = convert_from_path(pdf_path, first_page=start_page, last_page=end_page)

        # Process and concatenate images
        zoomed_images = []
        total_width = 0
        total_height = 0

        for image in images:
            zoomed_width = int(image.width * zoom_factor)
            zoomed_height = int(image.height * zoom_factor)
            zoomed_image = image.resize((zoomed_width, zoomed_height), Image.LANCZOS)
            if grayscale:
                zoomed_image = zoomed_image.convert("L")
            zoomed_images.append(zoomed_image)
            total_width = max(total_width, zoomed_width)
            total_height += zoomed_height

        # Create concatenated image
        concatenated_image = Image.new('RGB' if not grayscale else 'L', (total_width, total_height))

        current_y = 0
        for zoomed_image in zoomed_images:
            concatenated_image.paste(zoomed_image, (0, current_y))
            current_y += zoomed_image.height

        # Save optimized image
        concatenated_image = ImageOps.exif_transpose(concatenated_image)
        concatenated_image.save(output_path, "JPEG", quality=10, optimize=True)

        return output_file 