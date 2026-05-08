# Streamtrack 🚀

Streamtrack is a comprehensive Streamlit application designed to help you crush a 365-day challenge. It acts as your personal control center to track daily habits, monitor your weight journey, manage your finances, and keep an eye on your investment portfolio and financial goals.

## ✨ Features

* **🗓️ Daily Log:** 
  * Manage a customizable daily checklist of tasks (e.g., 10k Steps Walk, Study DSA, 3L Water).
  * Log your daily weight and add personal journal notes/observations.
* **📊 Analytics & History:** 
  * View activity trends and your weight journey over time with interactive Plotly charts.
  * Manage and edit your historical daily log data.
* **💸 Finance Tracker:** 
  * Track your daily income and expenses.
  * Auto-calculates your Total Income, Total Expenses, and Net Balance.
  * Visualize expenses by customizable categories in a dynamic pie chart.
* **📈 Portfolio & Financial Goals:** 
  * **Portfolio Dashboard:** Track investments across Stocks, Crypto, Real Estate, and more, including total invested vs. current value.
  * **Financial Goals:** Set saving targets (e.g., House Downpayment) and watch your progress grow with visual progress bars.

## 🗄️ Database Backends

Streamtrack provides two separate implementations based on your preference:
1. **`app.py` (Google Sheets):** Uses `gspread` to sync all your data to a cloud-based Google Spreadsheet, allowing you to access it anywhere.
2. **`app_with_db.py` (SQLite):** Uses a local `challenge.db` SQLite database for ultra-fast, local, and private data tracking.

## 🛠️ Setup & Installation

1. **Install Dependencies:**
   Make sure you have Python installed. Then, install the required packages:
   ```bash
   pip install streamlit pandas gspread google-auth plotly
   ```

2. **Configure Google Sheets Credentials (for `app.py` only):**
   * Create a Service Account in the Google Cloud Console.
   * Share your target Google Sheet with the Service Account email.
   * Create a `.streamlit/secrets.toml` file in the project root and add your connection details:
     ```toml
     [connections.gsheets]
     spreadsheet = "YOUR_GOOGLE_SHEET_URL"
     type = "service_account"
     project_id = "your-project-id"
     private_key = """-----BEGIN PRIVATE KEY-----
     ...
     -----END PRIVATE KEY-----"""
     client_email = "your-service-account@...iam.gserviceaccount.com"
     ```

   **🔄 Changing your Google Sheet or Service Account Email:**
   * If you need to switch to a different Google Sheet, simply update the `spreadsheet` URL in `.streamlit/secrets.toml`.
   * **Crucial Step:** Whenever you use a new sheet or update your `client_email`, you must click "Share" in the top right of your Google Sheet and share it with your specific `client_email` address, granting it **Editor** permissions.
   * If you generate a new Service Account, ensure you update both the `private_key` and `client_email` in your `.streamlit/secrets.toml` file to match the new credentials.

3. **Run the App:**
   ```bash
   streamlit run app.py
   # or
   streamlit run app_with_db.py
   ```