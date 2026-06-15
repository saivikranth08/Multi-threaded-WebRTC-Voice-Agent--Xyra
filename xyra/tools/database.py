# ─────────────────────────────────────────────
#  XYRA — Database Tools
#  Exposes contacts and profile operations to the LLM
# ─────────────────────────────────────────────

import logging
from xyra.db import db

logger = logging.getLogger("xyra.tools.database")


async def lookup_contact(name: str) -> str:
    """
    Search for a contact's details (phone, email, relationship) by name or relationship description (e.g., "father", "mother", "brother").
    Use this when the user asks for someone's contact details, or asks who a family member is.
    """
    if not db.pg_pool:
        return "❌ Database connection is not available."

    try:
        name_clean = name.strip().lower()
        # Clean common prefixes
        for filler in ["vickyy's ", "vickyy ", "user's ", "my "]:
            if name_clean.startswith(filler):
                name_clean = name_clean[len(filler):]

        if not name_clean:
            return "❌ Please provide a contact name or relationship to search for."
        async with db.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT name, phone, email, relationship 
                FROM contacts 
                WHERE LOWER(name) LIKE $1 OR LOWER(relationship) LIKE $1 
                LIMIT 1
                """,
                f"%{name_clean}%",
            )
            if row:
                parts = [f"Name: {row['name']}"]
                if row["relationship"]: parts.append(f"Relationship: {row['relationship']}")
                if row["phone"]:  parts.append(f"Phone: {row['phone']}")
                if row["email"]:  parts.append(f"Email: {row['email']}")
                return " | ".join(parts)
            else:
                return f"🔍 No contact found matching '{name}'. You can save it using 'add_contact'."
    except Exception as e:
        logger.error(f"Error looking up contact: {str(e)}")
        return f"❌ Database error: {str(e)}"


async def add_contact(name: str, email: str = "", phone: str = "") -> str:
    """
    Save or update a contact's email and/or phone number in the database.
    Use this when the user asks to save, add, or update a contact
    (e.g., "save John's email as john@example.com" or "save Prashant's number as 9876543210").
    """
    if not db.pg_pool:
        return "❌ Database connection is not available."

    try:
        name_clean  = name.strip()
        email_clean = email.strip().lower() or None
        phone_clean = phone.strip() or None
        async with db.pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO contacts (name, email, phone)
                VALUES ($1, $2, $3)
                ON CONFLICT (name) DO UPDATE SET
                    email = COALESCE(EXCLUDED.email, contacts.email),
                    phone = COALESCE(EXCLUDED.phone, contacts.phone);
            """, name_clean, email_clean, phone_clean)
            saved = []
            if email_clean: saved.append(f"email '{email_clean}'")
            if phone_clean: saved.append(f"phone '{phone_clean}'")
            return f"✅ Saved contact '{name_clean}' with {' and '.join(saved)}."
    except Exception as e:
        logger.error(f"Error adding contact: {str(e)}")
        return f"❌ Database error: {str(e)}"


async def get_user_fact(key: str) -> str:
    """
    Retrieve a fact or preference about the user from their profile (e.g., "first_name", "last_name", "timezone", "father", "mother", etc.).
    Use this when the user asks what you know about them, their details, or saved preferences.
    """
    if not db.pg_pool:
        return "❌ Database connection is not available."

    try:
        key_clean = key.strip().lower()
        # Clean common filler prefixes so the query is targeted
        for filler in ["vickyy's ", "vickyy ", "user's ", "my "]:
            if key_clean.startswith(filler):
                key_clean = key_clean[len(filler):]

        async with db.pg_pool.acquire() as conn:
            # First try exact match
            row = await conn.fetchrow(
                "SELECT value FROM user_profiles WHERE LOWER(key) = $1",
                key_clean,
            )
            # If not found, try fuzzy query
            if not row:
                row = await conn.fetchrow(
                    "SELECT value FROM user_profiles WHERE LOWER(key) LIKE $1 OR value LIKE $1 LIMIT 1",
                    f"%{key_clean}%",
                )

            if row:
                return f"👤 Stored preference for '{key_clean}': {row['value']}"
            else:
                return f"🔍 I couldn't find any profile details for '{key_clean}'."
    except Exception as e:
        logger.error(f"Error getting user fact: {str(e)}")
        return f"❌ Database error: {str(e)}"


async def save_user_fact(key: str, value: str) -> str:
    """
    Save or update a fact/preference about the user in their profile (e.g., save their name, city, favorite color, etc.).
    Use this when the user shares something about themselves, like "my favorite city is Paris" or "remember that my name is Sagar".
    """
    if not db.pg_pool:
        return "❌ Database connection is not available."

    try:
        key_clean = key.strip().lower()
        value_clean = value.strip()
        async with db.pg_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_profiles (key, value)
                VALUES ($1, $2)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
            """, key_clean, value_clean)
            return f"✅ Remembered: {key_clean} is now set to '{value_clean}'."
    except Exception as e:
        logger.error(f"Error saving user fact: {str(e)}")
        return f"❌ Database error: {str(e)}"
