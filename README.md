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

Run in the main directory of the project
```
python3 -m venv venv
source venv/bin/activate
```

Now you are working in a virtual environment. To install all dependencies for this project run:

```
pip install -r requirements.txt
```

If your contribution to the project changes the dependencies be sure to update them with:

```
pip freeze > requirements.txt
```

To exit the virtual environment:
```
deactivate
```
