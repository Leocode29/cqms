📊 Client Query Management System

A Streamlit-based web application to manage client queries efficiently, providing separate dashboards for Clients and Support staff. The project supports individual query submission, bulk CSV uploads, and advanced support analytics.

Features
Client Dashboard

Submit queries individually or via bulk CSV upload.

Upload screenshots for each query.

Real-time validation for email, mobile number, and required fields.

Support Dashboard

View and manage all client queries in an editable table.

Update query status (Open/Closed) with automatic resolution time calculation.

Download query data as CSV.

Analyze support metrics:

Average resolution time

Queries resolved within 24 hours

Total closed queries

Visual insights with charts for query types and backlog analysis.

General Features

User registration and login (Client & Support roles).

Session management with logout functionality.

Responsive Streamlit UI with forms, tables, and tabs.

Safe handling of image attachments.

Uses datetime for tracking query creation and closure.

Technology Stack

Frontend & UI: Streamlit

Backend & Database: MySQL / MariaDB (via Python DB API)

Language: Python 3.10+

Libraries: pandas, base64, re, datetime, Streamlit

Setup Instructions
1. Clone the Repository
git clone https://github.com/<your-username>/client-query-management.git
cd client-query-management

2. Install Dependencies
pip install -r requirements.txt

3. Database Setup

Create a database and queries table:

CREATE TABLE queries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_email VARCHAR(255),
    client_mobile VARCHAR(15),
    query_heading VARCHAR(255),
    query_description TEXT,
    status VARCHAR(50) DEFAULT 'Open',
    query_created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    query_closed_time DATETIME NULL,
    image LONGBLOB
);


Ensure a users table exists for authentication:

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(255),
    role ENUM('Client', 'Support')
);


Update db.py or connection settings with your database credentials.

4. Run the Application
streamlit run app.py


Access the app at http://localhost:8501

Usage

Register a new account (Client or Support).

Clients can submit queries via the form or bulk CSV.

Support staff can view, edit, and update query statuses.

Use the dashboard to track resolution metrics and query distributions.

Repository Structure
client-query-management/
│
├── app.py                  # Main Streamlit app
├── auth.py                 # User registration & login
├── client_page.py          # Client query submission logic
├── support_page.py         # Support query management logic
├── db.py                   # Database connection utility
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation