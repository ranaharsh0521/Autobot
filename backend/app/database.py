from sqlalchemy import create_engine, inspect, text  # type: ignore
from sqlalchemy.orm import sessionmaker, declarative_base  # type: ignore
from app.config import settings

# SQLite compatibility settings if using SQLite for local testing
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)
    # Check SQLite migrations for existing local db files
    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                inspector = inspect(engine)
                existing_tables = inspector.get_table_names()
                
                for table_name, table_obj in Base.metadata.tables.items():
                    if table_name in existing_tables:
                        existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
                        for col in table_obj.columns:
                            if col.name not in existing_cols:
                                col_type_str = str(col.type)
                                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type_str}"))
                conn.commit()
        except Exception:
            pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
