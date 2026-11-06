import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.environ.get("FINSIGHT_DB_PATH", "finsight.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import app.models.transaction
    import app.models.category_override
    import app.models.alert
    Base.metadata.create_all(bind=engine)

    # Safe SQLite column migration guard
    with engine.connect() as conn:
        try:
            result = conn.exec_driver_sql("PRAGMA table_info(transactions)").fetchall()
            existing_cols = {row[1] for row in result}
            new_columns = [
                ("source_page", "INTEGER DEFAULT 1"),
                ("source_row", "INTEGER"),
                ("raw_text", "TEXT DEFAULT ''"),
                ("extraction_confidence", "FLOAT DEFAULT 1.0"),
            ]
            for col_name, col_type in new_columns:
                if col_name not in existing_cols:
                    conn.exec_driver_sql(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type}")
            conn.commit()
        except Exception:
            pass

