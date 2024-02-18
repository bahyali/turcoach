# Turfcoach

A tool to schedule maintenance and replacement of grass in turfs depending on weather conditions.

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the Application
After adding configuring the database connection string to a new file called `.env` run the following command to run the server:

```bash
# Start the FastAPI server
uvicorn main:app --reload
```
This will start the FastAPI application with live reloading enabled.

Then navigate to `http://127.0.0.1:8000/docs` to view the API docs and test the endpoint.

## Running Tests

```bash
# Run pytest
pytest
```


## Built With

- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used
- [pytest](https://pytest.org/) - The testing framework used
- [Bunnet](https://github.com/roman-right/bunnet) - The ODM used