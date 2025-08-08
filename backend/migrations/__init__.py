import asyncio
import aiosqlite

async def run_migrations(db_path: str = "meeting_minutes.db"):
    """Run database migrations for the given SQLite database."""
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transcripts (
                id TEXT PRIMARY KEY,
                meeting_id TEXT NOT NULL,
                transcript TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                summary TEXT,
                action_items TEXT,
                key_points TEXT,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS summary_processes (
                meeting_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error TEXT,
                result TEXT,
                start_time TEXT,
                end_time TEXT,
                chunk_count INTEGER DEFAULT 0,
                processing_time REAL DEFAULT 0.0,
                metadata TEXT,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transcript_chunks (
                meeting_id TEXT PRIMARY KEY,
                meeting_name TEXT,
                transcript_text TEXT NOT NULL,
                model TEXT NOT NULL,
                model_name TEXT NOT NULL,
                chunk_size INTEGER,
                overlap INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                username TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                whisperModel TEXT NOT NULL,
                groqApiKey TEXT,
                openaiApiKey TEXT,
                anthropicApiKey TEXT,
                ollamaApiKey TEXT
            )
        """)
        await conn.commit()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--db", default="meeting_minutes.db", help="Path to SQLite database")
    args = parser.parse_args()
    asyncio.run(run_migrations(args.db))
