#!/bin/bash

# This script sets up a custom URL scheme to open PDFs at specific pages using the default PDF viewer.

# Step 1: Create the Python helper script to handle the custom URL scheme
cat << 'EOF' | sudo tee /usr/local/bin/open_pdf_page.py > /dev/null
#!/usr/bin/env python3
import re
import sys
import subprocess

def open_pdf(url):
    match = re.match(r'documentviewer://open\?file=([^&]+)&page=([0-9]+)', url)
    if match:
        file_path = match.group(1)
        page = match.group(2)
        file_path = re.sub(r'%20', ' ', file_path)  # Decode URL-encoded spaces
        # Open the PDF with the default PDF viewer
        subprocess.run(['xdg-open', file_path])

if __name__ == '__main__':
    if len(sys.argv) > 1:
        open_pdf(sys.argv[1])
EOF

# Make the Python script executable
sudo chmod +x /usr/local/bin/open_pdf_page.py

# Step 2: Create the desktop entry in the user's local applications directory
mkdir -p ~/.local/share/applications
cat << 'EOF' > ~/.local/share/applications/documentviewer-url-handler.desktop
[Desktop Entry]
Name=Document Viewer URL Handler
Exec=/usr/local/bin/open_pdf_page.py %u
Type=Application
MimeType=x-scheme-handler/documentviewer;
EOF

# Step 3: Update MIME types to register the custom URL scheme
xdg-mime default documentviewer-url-handler.desktop x-scheme-handler/documentviewer

echo "Setup complete. You can now use the custom URL scheme documentviewer://open?file=/path/to/your/file.pdf&page=page_number"

