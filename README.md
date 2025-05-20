Tug a Tools is a concept of a tool rental app. 
You can go on the app to find tools you need and when.
This submits a request and the suppliers of tug a tools will accept or counter your request and offer a quote. 
The app manages the full rental lifecycle to both the renter and rentee. 

## Running the example API

This repository includes a small FastAPI application located in `app/app.py`.
It uses SQLite for storage and offers endpoints for tool listings, bookings,
user registration, and more.

To run the API locally:

```bash
uvicorn app.app:app --reload
```

The server will start on `http://127.0.0.1:8000`. You can explore the API
interactively at `http://127.0.0.1:8000/docs`.

## Using the minimal frontend

The API also serves a basic HTML/JavaScript frontend for quick testing. Once the
server is running, open `http://127.0.0.1:8000/` in your browser. From there you
can register, log in, view tools and create bookings. Static assets are served
from `/static`.
