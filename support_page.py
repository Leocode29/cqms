from db import get_connection
from datetime import datetime, timezone
import pandas as pd
import traceback

# ─── Query Retrieval ─────────────────────────────────────────────
def get_queries():
    """Fetch all client queries for support dashboard."""
    try:
        conn = get_connection()
        if not conn:
            return pd.DataFrame()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, 
                    client_email,
                    client_mobile,        
                    query_heading, 
                    query_description, 
                    status, 
                    query_created_time, 
                    query_closed_time,
                    image
                FROM queries
                ORDER BY query_created_time DESC
            """)
            data = cursor.fetchall()

        conn.close()

        df = pd.DataFrame(data, columns=[
            "ID", "client_email", "client_mobile", "query_heading", 
            "query_description", "Status", "Created At", "Closed At", "Image"
        ])

        # Convert datetime safely
        for col in ["Created At", "Closed At"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        return df

    except Exception as e:
        print("❌ Error fetching queries:", e)
        traceback.print_exc()
        return pd.DataFrame()


# ─── Status Update ───────────────────────────────────────────────
def update_status(query_id, new_status):
    """Update query status and closed time if applicable."""
    try:
        conn = get_connection()
        if not conn:
            print("⚠️ Database connection failed.")
            return

        with conn.cursor() as cursor:
            if new_status.lower() == "closed":
                cursor.execute("""
                    UPDATE queries 
                    SET status = %s, query_closed_time = %s 
                    WHERE id = %s
                """, (new_status, datetime.now(timezone.utc), query_id))
            else:
                cursor.execute("""
                    UPDATE queries 
                    SET status = %s 
                    WHERE id = %s
                """, (new_status, query_id))
            conn.commit()

        conn.close()
        print(f"✅ Query ID {query_id} updated to {new_status}")

    except Exception as e:
        print(f"❌ Error updating status for Query ID {query_id}:", e)
        traceback.print_exc()


# ─── Support Metrics ─────────────────────────────────────────────
def get_support_metrics(df):
    """Compute basic support performance metrics."""
    if df.empty:
        return {"avg_resolution": None, "fast_resolved": 0, "total_closed": 0}

    df = df.copy()
    df["Resolution Time (hrs)"] = df.apply(
        lambda row: ((row["Closed At"] - row["Created At"]).total_seconds() / 3600)
        if pd.notnull(row["Closed At"]) else None,
        axis=1
    )

    resolved_df = df[df["Status"].str.lower() == "closed"]

    avg_resolution = resolved_df["Resolution Time (hrs)"].mean()
    fast_resolved = resolved_df[resolved_df["Resolution Time (hrs)"] <= 24].shape[0]
    total_closed = resolved_df.shape[0]

    return {
        "avg_resolution": avg_resolution,
        "fast_resolved": int(fast_resolved),
        "total_closed": int(total_closed)
    }


# ─── Query Type Distribution ─────────────────────────────────────
def get_query_distribution(df):
    """Return top 10 most frequent query types (by query_heading)."""
    if df.empty or "query_heading" not in df.columns:
        return pd.Series(dtype=int)
    return df["query_heading"].value_counts().head(10)
