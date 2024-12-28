import requests

def update_anki_source_links(highlights, new_pdf_path):
    anki_connect_url = "http://localhost:8765"
    pdf_name = new_pdf_path.split('/')[-1]
    for highlight in highlights:
        note_id = get_note_id_from_highlight(highlight)  # Assuming you have a way to get the note ID
        page = highlight[2]
        source_link = f'<a href="documentviewer://open?file={new_pdf_path}&page={page}">{pdf_name} (Page {page})</a>'
        update_note_source_link(anki_connect_url, note_id, source_link)

def get_note_id_from_highlight(highlight):
    # Implement logic to get note ID from highlight
    pass

def update_note_source_link(anki_connect_url, note_id, source_link):
    update_note = {
        "action": "updateNoteFields",
        "version": 6,
        "params": {
            "note": {
                "id": note_id,
                "fields": {
                    "SourceLink": source_link
                }
            }
        }
    }
    response = requests.post(anki_connect_url, json=update_note)
    if response.status_code == 200:
        print(f"Updated note {note_id} with new source link.")
    else:
        print(f"Failed to update note {note_id}. Response: {response.text}")

