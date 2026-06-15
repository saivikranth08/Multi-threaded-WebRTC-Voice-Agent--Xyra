# ─────────────────────────────────────────────
#  XYRA — Database Schema Initializer
#  Creates PostgreSQL tables and seeds Vickyy's profile and contacts
# ─────────────────────────────────────────────

import asyncio
import logging
from xyra.db import db

# Set up logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("xyra.db_init")


async def init_db(force: bool = False):
    logger.info("Starting database schema initialization...")
    try:
        # Connect to DB pools
        await db.connect()

        async with db.pg_pool.acquire() as conn:
            # 1. Enable pgvector extension
            logger.info("Enabling pgvector extension in PostgreSQL...")
            try:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                logger.info("✅ pgvector extension enabled.")
            except Exception as e:
                logger.warning(
                    f"⚠️ Could not enable pgvector (extension might not be supported/loaded): {str(e)}"
                )

            # Drop old tables ONLY if --force flag is passed
            if force:
                logger.warning("⚠️  --force flag detected. Dropping all existing tables...")
                await conn.execute("DROP TABLE IF EXISTS contacts CASCADE;")
                await conn.execute("DROP TABLE IF EXISTS user_profiles CASCADE;")
                await conn.execute("DROP TABLE IF EXISTS conversations CASCADE;")
                logger.warning("⚠️  Tables dropped. Recreating schema from scratch.")
            else:
                logger.info("Running in safe mode (no DROP). Use --force to wipe and recreate tables.")

            # 2. Create contacts lookup table (with phone and relationship)
            logger.info("Creating 'contacts' table...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE,
                    phone VARCHAR(50) UNIQUE,
                    relationship VARCHAR(100)
                );
            """)

            # 3. Create user profiles metadata table
            logger.info("Creating 'user_profiles' table...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(255) UNIQUE NOT NULL,
                    value TEXT NOT NULL
                );
            """)

            # 4. Create conversation logs table
            logger.info("Creating 'conversations' table...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    role VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL
                );
            """)

            # 5. Seed Vickyy's primary contacts
            logger.info("Seeding Vickyy's contacts...")
            await conn.executemany("""
                INSERT INTO contacts (name, email, phone, relationship)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (name) DO UPDATE SET 
                    email = EXCLUDED.email, 
                    phone = EXCLUDED.phone, 
                    relationship = EXCLUDED.relationship;
            """, [
                ("Ramesh", None, "9440113103", "father"),
                ("Lakshmi", None, "9492747677", "mother"),
                ("Rohit Annaya", "rohit@example.com", "6301443302", "brother"),
                ("Sai Annaya", "sai@example.com", "8977299683", "brother"),
                ("Vikranth Proton", "kanuruvikranth@proton.me", None, "self / test-account"),
                ("Vinnay", None, "8000444277", "college friend"),
                ("Shahistha Akka", None, "9849282625", "senior / sister")
            ])

            # 6. Seed Vickyy's profile metadata and facts
            logger.info("Seeding Vickyy's profile facts...")
            profile_facts = [
                ("first_name", "Sai Vikranth"),
                ("last_name", "Kanuru"),
                ("username", "Vickyy"),
                ("phone", "9398596589"),
                ("email", "kanuruvikranth@gmail.com"),
                ("location", "Vizianagaram, India"),
                ("timezone", "Asia/Kolkata"),
                ("temp_unit", "celsius"),
                ("college", "MVGR College of Engineering, Vizianagaram"),
                ("course", "B.Tech ECE (3rd Year)"),
                ("college_grad_year", "Expected May 2028"),
                ("backlogs", "One backlog in 2-1 (results are pending), and 2-2 regular exams results are also pending"),
                ("ece_interest", "Has no basic knowledge and no interest in ECE core subjects. Just wants to pass ECE academic subjects with a good CGPA. His inner core is filled with Generative and Agentic AI, which he studies and learns daily."),
                ("intermediate_school", "Narayana Junior College, Vizianagaram (MPC, May 2024, CGPA: 8.72)"),
                ("tenth_school", "Fort City School, Vizianagaram (SSC, March 2022, CGPA: 8.58)"),
                ("career_aim", "Get a job in Agentic AI / Generative AI"),
                ("skills", "Python, C, SQL (PostgreSQL, MySQL), LangChain, LangGraph, HuggingFace, FastAPI, Streamlit, Qdrant, FAISS, Chroma, Redis, Docker, LangSmith, GitHub"),
                ("fav_cricket_team", "Mumbai Indians"),
                ("reopening_date", "Monday, June 22nd, 2026"),
                ("routine_college", "9:15 AM to 3:00 PM (starts around 8:30 AM)"),
                ("routine_pavan_sir", "3:00 PM to 5:30/6:00 PM learning Gen/Agentic AI with Pavan sir in his cabin (ML enthusiast & guide)"),
                ("routine_core_work", "Starts around 7:30 PM (after relaxing/refreshing from 6:00/6:30 to 7:30 PM)"),
                ("routine_core_order", "Daily order: College works first, then DSA problems (easy to later stages), then System Design, and finally late-night core studies in Gen/Agentic AI"),
                ("relationship_senior_shahistha", "Shahistha Akka (supportive and inspiring senior/sister from Anantapur, lives in a PG near college)")
            ]

            await conn.executemany("""
                INSERT INTO user_profiles (key, value)
                VALUES ($1, $2)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
            """, profile_facts)

            logger.info("✅ Database successfully initialized with Vickyy's details!")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise e
    finally:
        await db.disconnect()
        logger.info("Database connection closed.")


if __name__ == "__main__":
    import sys
    force_flag = "--force" in sys.argv
    if force_flag:
        print("⚠️  WARNING: --force mode will DROP all existing tables and reseed from scratch.")
        confirm = input("Type 'yes' to confirm: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)
    asyncio.run(init_db(force=force_flag))
