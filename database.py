from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = URL.create(
    "postgresql+psycopg",
    username="postgres",
    password="TREWQ12345",
    host="127.0.0.1",
    port=5432,
    database="autoservice",
)

engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
