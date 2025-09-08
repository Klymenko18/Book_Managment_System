## Tech Stack

* Python 3.11+
* FastAPI
* SQLAlchemy 2.0
* Alembic
* PostgreSQL
* Pydantic
* Uvicorn

## API Documentation

* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Klymenko18/Book_Managment
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate 
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory:


Fill it with your local values. See `.env.example` below.


### 5. Apply database migrations

docker-compose exec web alembic revision --autogenerate -m "create tables"
docker-compose exec web alembic upgrade head


### 6. Build and run the project using Docker
docker-compose down && docker-compose build && docker-compose up
OR
docker-compose up --build --force-recreate

# 7 Test the code 
Locally - pytest

Insidre Docker - docker compose exec web pytest
