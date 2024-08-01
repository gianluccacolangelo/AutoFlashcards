import sqlite3

def main():
    db_path = "tracked_files.db"
    table_name = "tracked_files"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    create_tracked_files_table(cursor, table_name=table_name)
    create_highlights_table(cursor)

    conn.commit()
    conn.close()

def create_tracked_files_table(cursor, table_name="tracked_files"):
    try:
        cursor.execute(
            """
            CREATE TABLE tracked_files (
                inode INTEGER PRIMARY KEY,
                file_path TEXT NOT NULL,
                alias TEXT
            );
            """
        )
        print("Table 'tracked_files' was successfully created.")
    except sqlite3.Error as e:
        if 'already exists' in str(e):
            print(f"Table '{table_name}' already exists.")
        else:
            print(f"An error occurred: {e}")

def create_highlights_table(cursor):
    try:
        cursor.execute(
            """
            CREATE TABLE highlights (
                highlight_id TEXT PRIMARY KEY,
                pdf_id TEXT NOT NULL,
                page INTEGER NOT NULL,
                rect TEXT NOT NULL,
                text TEXT NOT NULL
            );
            """
        )
        print("Table 'highlights' was successfully created.")
    except sqlite3.Error as e:
        if 'already exists' in str(e):
            print("Table 'highlights' already exists.")
        else:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

