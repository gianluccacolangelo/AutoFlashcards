# 📚 AutoFlashcards

**Give me your highlighted book before you go to bed, and you'll have fresh, finely processed flashcards by the morning!**

## ✨ Features
- 🔍 Extracts highlights from PDF files
- 📝 Generates context around highlights
- 🤖 Creates flashcards using advanced language models (LLMs)
- 📥 Exports flashcards to Anki
- 🔄 Automatically updates flashcards when PDFs are moved or renamed
- 💾 Stores highlights in a SQLite database to avoid duplicates

## 🔑 Safely storing API_KEY

1. Create a `.env` file in the project root directory
2. Set your API key and preferred LLM provider in the `.env` file:
    ```env
    API_KEY=yourSuperSecretKey
    LLM_PROVIDER=gemini  # Options: gemini, openai, anthropic
    ```
3. Include `.env` in your `.gitignore` file

## 🛠️ Working on a virtual environment

### Using `venv`

Run in the main directory of the project:
```sh
python3 -m venv venv
source venv/bin/activate
```

To install all dependencies:
```sh
pip install -r requirements.txt
```

If you change the dependencies, update `requirements.txt`:
```sh
pip freeze > requirements.txt
```

To exit the virtual environment:
```sh
deactivate
```

### Using `conda`

Run in the main directory of the project:
```sh
conda env create -f environment.yml
conda activate myenv
```

To install all dependencies:
```sh
conda install --file requirements.txt
```

If you change the dependencies, update `environment.yml`:
```sh
conda env export --name myenv --file environment.yml
```

To exit the conda environment:
```sh
conda deactivate
```

## 🚀 Usage

1. Ensure your virtual environment is activated and dependencies are installed.
2. Run the main script with your PDF file:
    ```sh
    python main.py your_highlighted_book.pdf
    ```

## 📝 Notes
- Ensure that the directory you want to monitor has the necessary read/write permissions.
- You can modify the `DATABASE_PATH` and `TABLE_NAME` variables in the scripts to customize the database location and table name.

