# AutoFlashcards
Give me your highlighted book before you go to bed, and you'll have fresh, finely processed flashcards by the morning

## Safely storing API_KEY

1. Create a .env file
2. Save your API_KEY using key=value format:
    ```
    API_KEY="yourSuperSecretKey"
    ```
3. Include .env in .gitignore

## Working on a virtual environment

### Using `venv`

Run in the main directory of the project:
```
python3 -m venv venv
source venv/bin/activate
```

To install all dependencies:
```
pip install -r requirements.txt
```

If you change the dependencies, update `requirements.txt`:
```
pip freeze > requirements.txt
```

To exit the virtual environment:
```
deactivate
```

### Using `conda`

Run in the main directory of the project:
```
conda env create -f environment.yml
conda activate myenv
```

To install all dependencies:
```
conda install --file requirements.txt
```

If you change the dependencies, update `environment.yml`:
```
conda env export --name myenv --file environment.yml
```

To exit the conda environment:
```
conda deactivate
```
