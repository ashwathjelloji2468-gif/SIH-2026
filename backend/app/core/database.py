from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine_kwargs = {
    "connect_args": connect_args,
    "echo": False,
}

if not is_sqlite:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_pre_ping": True,
    })

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def sync_schema(target_engine=None):
    """Auto-add missing columns and sync column nullability for SQLite tables based on SQLAlchemy models."""
    import app.models.db_models  # ensure models are registered with Base
    from sqlalchemy import inspect, text
    from sqlalchemy.schema import CreateTable

    eng = target_engine or engine
    inspector = inspect(eng)

    with eng.connect() as conn:
        # 1. Auto-add missing columns to existing tables
        for table_name, table in Base.metadata.tables.items():
            if inspector.has_table(table_name):
                existing_cols = {c['name'] for c in inspector.get_columns(table_name)}
                for col in table.columns:
                    if col.name not in existing_cols:
                        col_type = col.type.compile(eng.dialect)
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type};"))

        # 2. Fix threat_scenarios column nullability drift if notnull=1 for target nullable columns
        if inspector.has_table("threat_scenarios"):
            db_cols = inspector.get_columns("threat_scenarios")
            target_cols = {"quantum_threat_horizon_year", "data_lifetime_years", "migration_time_years"}
            needs_migration = any(
                c["name"] in target_cols and not c["nullable"]
                for c in db_cols
            )
            if needs_migration:
                from app.models.db_models import ThreatScenario
                from sqlalchemy.schema import CreateIndex

                table = ThreatScenario.__table__
                # Save existing indexes and triggers before rebuild
                existing_indexes = inspector.get_indexes("threat_scenarios")
                triggers = conn.execute(text("SELECT name, sql FROM sqlite_master WHERE tbl_name = 'threat_scenarios' AND type = 'trigger' AND sql IS NOT NULL;")).fetchall()

                ddl = str(CreateTable(table).compile(dialect=eng.dialect))
                ddl_new = ddl.replace("CREATE TABLE threat_scenarios (", "CREATE TABLE threat_scenarios_new (", 1)
                
                existing_col_names = [c["name"] for c in db_cols]
                col_list_str = ", ".join(existing_col_names)

                conn.execute(text("PRAGMA foreign_keys=OFF;"))
                conn.execute(text(ddl_new))
                conn.execute(text(f"INSERT INTO threat_scenarios_new ({col_list_str}) SELECT {col_list_str} FROM threat_scenarios;"))
                conn.execute(text("DROP TABLE threat_scenarios;"))
                conn.execute(text("ALTER TABLE threat_scenarios_new RENAME TO threat_scenarios;"))

                # Re-create ORM indexes
                for idx in table.indexes:
                    try:
                        idx_sql = str(CreateIndex(idx).compile(dialect=eng.dialect))
                        conn.execute(text(f"{idx_sql};"))
                    except Exception:
                        pass

                # Re-create pre-existing database indexes
                for idx in existing_indexes:
                    if not idx.get("duplicates_constraint"):
                        idx_name = idx["name"]
                        unique_str = "UNIQUE " if idx.get("unique") else ""
                        cols_str = ", ".join([f'"{col}"' for col in idx["column_names"]])
                        conn.execute(text(f"CREATE {unique_str}INDEX IF NOT EXISTS \"{idx_name}\" ON threat_scenarios ({cols_str});"))

                # Re-create pre-existing triggers
                for trg_name, trg_sql in triggers:
                    if trg_sql:
                        conn.execute(text(f"{trg_sql};"))

                conn.execute(text("PRAGMA foreign_keys=ON;"))

        conn.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

