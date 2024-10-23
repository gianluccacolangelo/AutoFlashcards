# highlight_manager.py

import sqlite3
import os
from pdf_handler import PDFHandler

class HighlightManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def delete_highlight_history(self, pdf_path):
        pdf_handler = PDFHandler(pdf_path)
        pdf_id = pdf_handler.pdf_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM highlights WHERE pdf_id = ?", (pdf_id,))
            conn.commit()
            deleted_count = cursor.rowcount
            print(f"Deleted {deleted_count} highlight(s) for PDF: {pdf_path}")
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()

    def get_highlight_count(self, pdf_path):
        pdf_handler = PDFHandler(pdf_path)
        pdf_id = pdf_handler.pdf_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM highlights WHERE pdf_id = ?", (pdf_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return 0
        finally:
            conn.close()

    def delete_last_n_highlights(self, pdf_path, n=1):
        pdf_handler = PDFHandler(pdf_path)
        pdf_id = pdf_handler.pdf_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Get the last n highlight IDs for this PDF
            cursor.execute("""
                DELETE FROM highlights 
                WHERE highlight_id IN (
                    SELECT highlight_id 
                    FROM highlights 
                    WHERE pdf_id = ? 
                    ORDER BY ROWID DESC 
                    LIMIT ?
                )
            """, (pdf_id, n))
            
            conn.commit()
            deleted_count = cursor.rowcount
            print(f"Deleted last {deleted_count} highlight(s) for PDF: {pdf_path}")
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
        finally:
            conn.close()
