from db import get_connection
from datetime import datetime, timezone
import pandas as pd
import traceback

# ─── Single Query Submission ─────────────────────────────────────
def submit_query_to_db(client_email, client_mobile, query_heading, query_description, image=None):
    """Submit a single client query to the database."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return "⚠️ Database connection failed"

        # Read image safely (reset pointer if already read once)
        img_data = None
        if image:
            try:
                image.seek(0)
                img_data = image.read()
            except Exception:
                img_data = None

        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO queries (client_email, client_mobile, query_heading, query_description, image, status, query_created_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                client_email.strip() if client_email else None,
                str(client_mobile).strip() if client_mobile else None,
                query_heading.strip() if query_heading else None,
                query_description.strip() if query_description else None,
                img_data,
                "Open",
                datetime.now(timezone.utc)
            ))
            conn.commit()

        return "✅ Query submitted successfully"

    except Exception as e:
        print("❌ Error submitting query:", e)
        traceback.print_exc()
        return f"Error: {e}"

    finally:
        if conn:
            conn.close()


# ─── Bulk Query Submission ───────────────────────────────────────
def submit_bulk_queries(df):
    """Bulk upload client queries from a DataFrame."""
    conn = None
    try:
        if df.empty:
            return "⚠️ No data found to insert"

        required_columns = {"client_email", "client_mobile", "query_heading", "query_description"}
        if not required_columns.issubset(df.columns):
            return "⚠️ Missing required columns in uploaded data"

        conn = get_connection()
        if not conn:
            return "⚠️ Database connection failed"

        with conn.cursor() as cursor:
            records = [
                (
                    str(row["client_email"]).strip(),
                    str(row["client_mobile"]).strip(),
                    str(row["query_heading"]).strip(),
                    str(row["query_description"]).strip(),
                    None,  # No image in bulk mode
                    "Open",
                    datetime.now(timezone.utc)
                )
                for _, row in df.iterrows()
            ]
            cursor.executemany("""
                INSERT INTO queries (client_email, client_mobile, query_heading, query_description, image, status, query_created_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, records)

        conn.commit()
        return f"✅ {len(df)} queries uploaded successfully"

    except Exception as e:
        print("❌ Error during bulk insert:", e)
        traceback.print_exc()
        return f"Error: {e}"

    finally:
        if conn:
            conn.close()
