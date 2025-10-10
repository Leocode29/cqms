import streamlit as st
import pandas as pd
import re
import base64
from datetime import datetime

from auth import create_user, login_user, check_user_exists
from client_page import submit_query_to_db, submit_bulk_queries
from support_page import get_queries, update_status, get_support_metrics, get_query_distribution

# ─── Utility: Convert Blob to Image ─────────────────────────────
def blob_to_data_url(blob_bytes: bytes, mime_type: str = "image/png") -> str:
    encoded = base64.b64encode(blob_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

# ─── Page Config ────────────────────────────────────────────────
st.set_page_config(page_title="Client Query Management", layout="wide")

# Apply CSS for full-width buttons and editors
st.markdown("""
<style>
div.stButton > button, div.stDownloadButton > button {
    width: 100%;
    border-radius: 8px;
    height: 2.5em;
    font-weight: 600;
}
.stDataFrame, .stDataEditor {
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Session Initialization ─────────────────────────────────────
st.session_state.setdefault("role", None)
st.session_state.setdefault("page", "home")
st.session_state.setdefault("username", "")

# ───    Handler ─────────────────────────────────────────────
def logout():
    st.session_state.clear()

# ─── Login / Registration ───────────────────────────────────────
if st.session_state.role is None:
    st.title("🔐 Client Query Management System")
    choice = st.sidebar.radio("Select Option", ["Login", "Register"])

    if choice == "Register":
        st.subheader("📝 Create New Account")
        with st.form("register_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            role = st.selectbox("Role", ["Client", "Support"])
            submitted = st.form_submit_button("Register")

            if submitted:
                if password != confirm:
                    st.warning("⚠️ Passwords do not match.")
                elif check_user_exists(username):
                    st.warning("⚠️ Username already exists.")
                else:
                    create_user(username, password, role)
                    st.success("✅ Account created! Please log in.")

    else:
        st.subheader("🔑 Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                role = login_user(username, password)
                if role:
                    st.session_state.role = role
                    st.session_state.username = username
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

# ─── Role-Based Dashboard ───────────────────────────────────────
else:
    top_col1, top_col2 = st.columns([10, 1])
    with top_col2:
        st.button("Logout", on_click=logout)

    st.title("📊 Client Query Management System")
    st.write(f"Welcome, **{st.session_state.username} ({st.session_state.role})**!")

    # ─── Home Page ───────────────────────────────────────────────
    if st.session_state.page == "home":
        if st.session_state.role == "Client":
            st.button("📝 Submit a New Query", on_click=lambda: st.session_state.update({"page": "submit_query"}))
        elif st.session_state.role == "Support":
            st.button("🛠️ View and Manage Queries", on_click=lambda: st.session_state.update({"page": "view_queries"}))

    # ─── Client Query Submission ────────────────────────────────
    elif st.session_state.page == "submit_query":
        st.subheader("📝 Client Query Submission")
        tab1, tab2 = st.tabs(["📝 Individual Query", "📥 Bulk Upload"])

        # ─── Individual Query ─────────────────────────────
        with tab1:
            with st.form("query_form"):
                client_email = st.text_input("Your Email")
                client_mobile = st.text_input("Mobile Number")
                query_heading = st.text_input("Query Heading")
                query_description = st.text_area("Describe your issue")
                image = st.file_uploader("Upload Screenshot (optional)", type=["png", "jpg", "jpeg"])
                submitted = st.form_submit_button("Submit Query")

                if submitted:
                    # Validation
                    if not re.match(r"[^@]+@[^@]+\.[^@]+", client_email):
                        st.warning("⚠️ Invalid email format.")
                    elif not client_mobile.isdigit() or len(client_mobile) != 10:
                        st.warning("⚠️ Invalid client_mobile number.")
                    elif not query_heading.strip() or not query_description.strip():
                        st.warning("⚠️ query_heading and query_description cannot be empty.")
                    else:
                        result = submit_query_to_db(client_email, client_mobile, query_heading, query_description, image)
                        if result and isinstance(result, str) and "success" in result.lower():
                            st.success("✅ Query submitted successfully!")
                        else:
                            st.error(f"❌ Submission failed: {result or 'Unknown error'}")

        # ─── Bulk Upload ─────────────────────────────
        with tab2:
            uploaded_file = st.file_uploader("Upload CSV File", type="csv", key="csv_upload")
            if uploaded_file:
                df = pd.read_csv(uploaded_file)
                required_cols = {"client_email", "client_mobile", "query_heading", "query_description"}
                if not required_cols.issubset(df.columns):
                    st.error("❌ CSV must contain Email, client_mobile, query_heading, and query_description columns.")
                elif df.empty:
                    st.warning("⚠️ Uploaded CSV is empty.")
                else:
                    st.dataframe(df.head())
                    if st.button("Upload Queries"):
                        result = submit_bulk_queries(df)
                        if result and isinstance(result, str) and "success" in result.lower():
                            st.success("✅ Queries uploaded successfully!")
                        else:
                            st.error(f"❌ Upload failed: {result or 'Unknown error'}")

        st.button("⬅️ Back to Home", on_click=lambda: st.session_state.update({"page": "home"}))

    # ─── Support Dashboard ────────────────────────────────
    elif st.session_state.page == "view_queries":
        try:
            queries_df = get_queries()
        except Exception as e:
            st.error(f"❌ Failed to fetch queries: {e}")
            queries_df = pd.DataFrame()

        if queries_df is None or queries_df.empty:
            st.info("📭 No queries to display.")
            if st.button("⬅️ Back to Home"):
                st.session_state.page = "home"
        else:
            # Compute resolution time
            queries_df["Resolution Time (hrs)"] = queries_df.apply(
                lambda row: ((row["Closed At"] - row["Created At"]).total_seconds() / 3600)
                if pd.notnull(row["Closed At"]) else None,
                axis=1
            )

            tab1, tab2 = st.tabs(["📋 Query Table", "📊 Support Metrics"])

            # ─── TAB 1: Query Table ───────────────────────────────
            with tab1:
                search_term = st.text_input("🔍 Search by client_email or query_heading")
                filtered_df = queries_df.copy()
                if search_term:
                    filtered_df = filtered_df[
                        filtered_df["client_email"].str.contains(search_term, case=False, na=False) |
                        filtered_df["query_heading"].str.contains(search_term, case=False, na=False)
                    ]

                st.download_button(
                    "📥 Export to CSV",
                    filtered_df.to_csv(index=False),
                    "queries.csv",
                    "text/csv"
                )

                # Attachment handling
                if "Image" in filtered_df.columns:
                    filtered_df["Attachment"] = filtered_df["Image"].apply(
                        lambda blob: f"[📎 View](data:image/png;base64,{base64.b64encode(blob).decode()})"
                        if pd.notnull(blob) else "—"
                    )
                    filtered_df = filtered_df.drop(columns=["Image"])
                else:
                    filtered_df["Attachment"] = "—"

                edited_df = st.data_editor(
                    filtered_df,
                    column_config={
                        "Status": st.column_config.SelectboxColumn(
                            "Status", options=["Open", "Closed"]
                        ),
                        "Attachment": st.column_config.TextColumn(
                            "Attachment", help="Click to view the uploaded attachment"
                        )
                    },
                    hide_index=True,
                    disabled=["ID", "Created At", "Closed At", "Resolution Time (hrs)", "client_description", "Attachment"],
                    key="query_table_editor"
                )

                # Detect and update status changes
                status_changed = False
                for original, edited in zip(filtered_df.itertuples(), edited_df.itertuples()):
                    if original.Status != edited.Status:
                        update_status(edited.ID, edited.Status)
                        status_changed = True

                if status_changed:
                    st.success("✅ Query status updated successfully!")

            # ─── TAB 2: Support Metrics ─────────────────────────────
            with tab2:
                metrics = get_support_metrics(queries_df)
                st.metric("📈 Avg Resolution Time (hrs)", 
                          f"{metrics['avg_resolution']:.2f}" if metrics['avg_resolution'] else "N/A")
                st.metric("⚡ Fast Resolutions (<24 hrs)", metrics["fast_resolved"])
                st.metric("✅ Total Closed Queries", metrics["total_closed"])

                st.markdown("### 🔍 Most Common Query Types")
                top_issues = get_query_distribution(queries_df)
                st.bar_chart(top_issues)

                st.markdown("### 🕒 Backlog Insights")
                backlog = queries_df[
                    (queries_df["Status"] == "Open") &
                    (queries_df["Created At"] < pd.Timestamp.now() - pd.Timedelta(days=3))
                ]
                st.write(f"📌 {backlog.shape[0]} queries pending for more than 3 days")

            # Back to Home button
            if st.button("⬅️ Back to Home"):
                st.session_state.page = "home"
                st.rerun()
