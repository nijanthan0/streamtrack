import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import plotly.express as px
import requests
import threading
import time
import schedule

# --- CONFIGURATION ---


# --- DATABASE ENGINE ---
def init_db():
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (day_num INTEGER PRIMARY KEY, log_date TEXT, tasks_completed INTEGER, weight REAL, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS task_list (id INTEGER PRIMARY KEY, task_name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS finance_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, f_date TEXT, type TEXT, category TEXT, amount REAL, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, asset_name TEXT, asset_type TEXT, invested_amount REAL, current_value REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, goal_name TEXT, goal_type TEXT, target_amount REAL, current_amount REAL, target_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS short_term_goals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, goal_name TEXT, target_date TEXT, tasks TEXT, completed_tasks TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS schedules 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, reminder_time TEXT, message TEXT, title TEXT)''')

    # Migrations & Seeding
    try:
        c.execute("SELECT weight FROM logs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE logs ADD COLUMN weight REAL DEFAULT 92.0")
    try:
        c.execute("SELECT log_date FROM logs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE logs ADD COLUMN log_date TEXT")
        
    try:
        c.execute("SELECT goal_type FROM goals LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE goals ADD COLUMN goal_type TEXT DEFAULT 'Cash'")

    try:
        c.execute("SELECT completed_tasks FROM logs LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE logs ADD COLUMN completed_tasks TEXT")

    c.execute("SELECT COUNT(*) FROM task_list")
    if c.fetchone()[0] == 0:
        seed_tasks = ["10k Steps Walk", "Study DSA (1 Hour)", "3L Water", "Intermittent Fasting"]
        for t in seed_tasks:
            c.execute("INSERT INTO task_list (task_name) VALUES (?)", (t,))
            
    c.execute("SELECT COUNT(*) FROM schedules")
    if c.fetchone()[0] == 0:
        seed_schedules = [
            ("07:00", "Time to wash your face and brush your teeth! 🪥", "Morning Routine ☀️"),
            ("10:00", "Time to learn DSA and do job prep! 💻", "Study Time 📚"),
            ("18:00", "Time to prepare public speaking skills! 🎤", "Skill Prep 🗣️")
        ]
        for s in seed_schedules:
            c.execute("INSERT INTO schedules (reminder_time, message, title) VALUES (?, ?, ?)", s)
    conn.commit()
    conn.close()


# --- HELPER FUNCTIONS ---
def get_dynamic_tasks():
    conn = sqlite3.connect('challenge.db')
    df = pd.read_sql_query("SELECT * FROM task_list", conn)
    conn.close()
    return df


def add_task(name):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("INSERT INTO task_list (task_name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def delete_task(t_id):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("DELETE FROM task_list WHERE id = ?", (t_id,))
    conn.commit()
    conn.close()


def get_finance_data():
    conn = sqlite3.connect('challenge.db')
    df = pd.read_sql_query("SELECT * FROM finance_logs", conn)
    conn.close()
    return df

def add_finance_record(f_date, f_type, category, amount, notes):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("INSERT INTO finance_logs (f_date, type, category, amount, notes) VALUES (?, ?, ?, ?, ?)",
              (f_date, f_type, category, amount, notes))
    conn.commit()
    conn.close()

def delete_finance_record(f_id):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("DELETE FROM finance_logs WHERE id = ?", (f_id,))
    conn.commit()
    conn.close()

def get_portfolio_data():
    conn = sqlite3.connect('challenge.db')
    df = pd.read_sql_query("SELECT * FROM portfolio", conn)
    conn.close()
    return df

def add_portfolio_asset(asset_name, asset_type, invested_amount, current_value):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("INSERT INTO portfolio (asset_name, asset_type, invested_amount, current_value) VALUES (?, ?, ?, ?)", (asset_name, asset_type, invested_amount, current_value))
    conn.commit()
    conn.close()

def delete_portfolio_asset(p_id):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("DELETE FROM portfolio WHERE id = ?", (p_id,))
    conn.commit()
    conn.close()

def get_goals_data():
    conn = sqlite3.connect('challenge.db')
    df = pd.read_sql_query("SELECT * FROM goals", conn)
    conn.close()
    return df

def add_financial_goal(goal_name, goal_type, target_amount, current_amount, target_date):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("INSERT INTO goals (goal_name, goal_type, target_amount, current_amount, target_date) VALUES (?, ?, ?, ?, ?)", (goal_name, goal_type, target_amount, current_amount, target_date))
    conn.commit()
    conn.close()

def delete_financial_goal(g_id):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("DELETE FROM goals WHERE id = ?", (g_id,))
    conn.commit()
    conn.close()

def edit_portfolio_asset(p_id, asset_name, asset_type, invested_amount, current_value):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("UPDATE portfolio SET asset_name = ?, asset_type = ?, invested_amount = ?, current_value = ? WHERE id = ?", (asset_name, asset_type, invested_amount, current_value, p_id))
    conn.commit()
    conn.close()

def edit_financial_goal(g_id, goal_name, goal_type, target_amount, current_amount, target_date):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("UPDATE goals SET goal_name = ?, goal_type = ?, target_amount = ?, current_amount = ?, target_date = ? WHERE id = ?", (goal_name, goal_type, target_amount, current_amount, str(target_date), g_id))
    conn.commit()
    conn.close()

def save_log(day, log_date, score, completed_tasks, weight, note):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO logs (day_num, log_date, tasks_completed, completed_tasks, weight, notes) VALUES (?, ?, ?, ?, ?, ?)",
              (day, log_date, score, completed_tasks, weight, note))
    conn.commit()
    conn.close()


def delete_log_entry(day_n):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("DELETE FROM logs WHERE day_num = ?", (day_n,))
    conn.commit()
    conn.close()


def get_existing_log(day_n):
    conn = sqlite3.connect('challenge.db')
    df = pd.read_sql_query(f"SELECT * FROM logs WHERE day_num = {day_n}", conn)
    conn.close()
    return df


def get_short_term_goals():
    conn = sqlite3.connect('challenge.db')
    df = pd.read_sql_query("SELECT * FROM short_term_goals", conn)
    conn.close()
    return df


def add_short_term_goal(goal_name, target_date, tasks):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("INSERT INTO short_term_goals (goal_name, target_date, tasks, completed_tasks) VALUES (?, ?, ?, ?)", (goal_name, target_date, tasks, ""))
    conn.commit()
    conn.close()


def delete_short_term_goal(g_id):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("DELETE FROM short_term_goals WHERE id = ?", (g_id,))
    conn.commit()
    conn.close()


def update_short_term_goal_tasks(g_id, completed_tasks):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("UPDATE short_term_goals SET completed_tasks = ? WHERE id = ?", (completed_tasks, g_id))
    conn.commit()
    conn.close()


def edit_short_term_goal(g_id, goal_name, target_date, tasks):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("UPDATE short_term_goals SET goal_name = ?, target_date = ?, tasks = ? WHERE id = ?", (goal_name, target_date, tasks, g_id))
    conn.commit()
    conn.close()

def get_schedules():
    conn = sqlite3.connect('challenge.db')
    df = pd.read_sql_query("SELECT * FROM schedules", conn)
    conn.close()
    return df

def add_schedule(reminder_time, message, title):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("INSERT INTO schedules (reminder_time, message, title) VALUES (?, ?, ?)", (reminder_time, message, title))
    conn.commit()
    conn.close()

def delete_schedule(s_id):
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE id = ?", (s_id,))
    conn.commit()
    conn.close()

# --- BACKGROUND REMINDER SERVICE ---
class ReminderService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReminderService, cls).__new__(cls)
            cls._instance.thread = None
            cls._instance.stop_event = threading.Event()
            cls._instance.topic = "my_streamtrack_reminders"
        return cls._instance

    def start(self, topic):
        self.topic = topic
        # Only start a new thread if one isn't already running
        if self.thread is None or not self.thread.is_alive():
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            
            schedule.clear()
            conn = sqlite3.connect('challenge.db')
            df = pd.read_sql_query("SELECT * FROM schedules", conn)
            conn.close()
            for _, row in df.iterrows():
                try:
                    schedule.every().day.at(row['reminder_time']).do(self.send_reminder, row['message'], row['title'])
                except Exception:
                    pass

    def _run(self):
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)

    def send_reminder(self, message, title):
        try:
            requests.post(f"https://ntfy.sh/{self.topic}", data=message.encode('utf-8'), headers={"Title": title.encode('utf-8')})
        except Exception:
            pass

@st.cache_resource
def get_reminder_service():
    return ReminderService()

reminders = get_reminder_service()

init_db()

# --- SIDEBAR: NAVIGATION & TASK MANAGER ---
st.sidebar.title("🗓️ Control Center")
challenge_start_date = st.sidebar.date_input("Challenge Start Date", value=date(2026, 5, 7))
challenge_end_date = st.sidebar.date_input("Challenge End Date", value=date(2027, 5, 7))
target_weight = st.sidebar.number_input("Target Weight Goal (kg)", value=82.0, step=0.1)
selected_date = st.sidebar.date_input("Select Date", value=date.today())
page = st.sidebar.radio("View", ["Daily Log", "Analytics & History", "Finance Tracker", "Portfolio & Goals", "Short-Term Goals", "Reminders Schedule"])

st.sidebar.divider()
st.sidebar.subheader("⚙️ Manage Checklist")
new_task = st.sidebar.text_input("New task name...")
if st.sidebar.button("Add to Checklist"):
    if new_task:
        add_task(new_task)
        st.rerun()

all_tasks = get_dynamic_tasks()
for _, row in all_tasks.iterrows():
    col_t, col_b = st.sidebar.columns([4, 1])
    col_t.write(f"• {row['task_name']}")
    if col_b.button("🗑️", key=f"del_task_{row['id']}"):
        delete_task(row['id'])
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("🔔 Reminders (ntfy.sh)")
ntfy_topic = st.sidebar.text_input("ntfy Topic Name", value="my_streamtrack_reminders", help="Install the ntfy app on your phone and subscribe to this topic name.")

if st.sidebar.button("▶️ Start Auto-Reminders", use_container_width=True):
    reminders.start(ntfy_topic)
    st.sidebar.success("Started! 🕒")

if st.sidebar.button("✉️ Send Test Notification", use_container_width=True):
    reminders.topic = ntfy_topic
    reminders.send_reminder("This is a test reminder from Streamtrack! 🚀", "Test Reminder")
    st.sidebar.success("Test sent!")

st.sidebar.caption("Note: The app must remain running in your terminal for automated reminders to trigger at scheduled times.")

active_day_num = (selected_date - challenge_start_date).days + 1
TOTAL_DAYS = (challenge_end_date - challenge_start_date).days

# --- PAGE 1: DAILY LOG ---
if page == "Daily Log":
    st.title(f"🚀 Day {active_day_num} of {TOTAL_DAYS}")
    st.write(f"**Logging for:** {selected_date.strftime('%A, %B %d, %Y')}")

    existing_df = get_existing_log(active_day_num)
    has_data = not existing_df.empty

    val_w = float(existing_df['weight'].iloc[0]) if has_data else 92.0
    val_note = existing_df['notes'].iloc[0] if has_data else ""
    val_score = int(existing_df['tasks_completed'].iloc[0]) if has_data else 0
    
    if has_data and 'completed_tasks' in existing_df.columns and pd.notna(existing_df['completed_tasks'].iloc[0]):
        val_completed_tasks = [t.strip() for t in str(existing_df['completed_tasks'].iloc[0]).split(",") if t.strip()]
    else:
        val_completed_tasks = []

    col1, col2 = st.columns(2)
    with col1:
        current_w = st.number_input("Current Weight (kg)", value=val_w, step=0.1)
    with col2:
        st.metric(f"Goal: {target_weight} kg", f"{current_w} kg", delta=f"{target_weight - current_w:.1f} kg")

    st.subheader("Daily Checklist")
    current_task_names = all_tasks['task_name'].tolist()

    if has_data:
        st.info(f"Previously logged score: {val_score}/{len(current_task_names)}")

    checked_tasks = [st.checkbox(t, value=(t in val_completed_tasks), key=f"c_{t}_{active_day_num}") for t in current_task_names]
    score = sum(checked_tasks)
    completed_task_names = [t for t, c in zip(current_task_names, checked_tasks) if c]

    st.subheader("Journal")
    user_note = st.text_area("Observations:", value=val_note)

    if st.button("Save Entry"):
        save_log(active_day_num, selected_date.isoformat(), score, ", ".join(completed_task_names), current_w, user_note)
        st.balloons()
        st.success(f"Day {active_day_num} recorded!")

# --- PAGE 2: ANALYTICS & HISTORY ---
elif page == "Analytics & History":
    st.title("📊 Progress Analytics")
    conn = sqlite3.connect('challenge.db')
    hist_df = pd.read_sql_query("SELECT * FROM logs ORDER BY day_num ASC", conn)
    conn.close()

    if not hist_df.empty:
        # Charts
        st.plotly_chart(px.line(hist_df, x="day_num", y="tasks_completed", title="Activity Trend", markers=True),
                        use_container_width=True)
        fig_w = px.line(hist_df, x="day_num", y="weight", title="Weight Journey", markers=True)
        fig_w.add_hline(y=target_weight, line_dash="dash", line_color="green", annotation_text=f"Target {target_weight}kg")
        st.plotly_chart(fig_w, use_container_width=True)

        st.divider()
        st.subheader("Manage Historical Data")

        # Log Deletion Section
        log_to_delete = st.selectbox("Select Day to Delete:", hist_df['day_num'].unique())
        if st.button("❌ Delete Selected Day Log"):
            delete_log_entry(log_to_delete)
            st.warning(f"Day {log_to_delete} log has been deleted.")
            st.rerun()

        st.subheader("Raw Data Table")
        st.dataframe(hist_df.sort_values(by="day_num", ascending=False), use_container_width=True)
    else:
        st.warning("No data logged yet.")

# --- PAGE 3: FINANCE TRACKER ---
elif page == "Finance Tracker":
    st.title("💸 Finance Tracker")

    with st.expander("➕ Add New Transaction", expanded=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            f_date = st.date_input("Date", value=date.today(), key="f_date")
            f_type = st.selectbox("Type", ["Expense", "Income"])
            f_amount = st.number_input("Amount", min_value=0.0, step=10.0)
        with f_col2:
            categories = ["Food", "Transport", "Rent/Mortgage", "Salary", "Utilities", "Entertainment", "Other"]
            f_category = st.selectbox("Category", categories)
            f_notes = st.text_input("Notes (Optional)")

        if st.button("Add Transaction"):
            add_finance_record(f_date, f_type, f_category, f_amount, f_notes)
            st.success("Transaction added!")
            st.rerun()

    st.divider()
    st.subheader("Dashboard")

    finance_df = get_finance_data()

    if not finance_df.empty:
        finance_df['amount'] = pd.to_numeric(finance_df['amount'])
        finance_df['f_date'] = pd.to_datetime(finance_df['f_date'], errors='coerce')
        finance_df['month_year'] = finance_df['f_date'].dt.strftime('%Y-%m')

        months = ["All Time"] + sorted([m for m in finance_df['month_year'].unique() if pd.notna(m)], reverse=True)
        selected_month = st.selectbox("Filter by Month", months)

        if selected_month != "All Time":
            filtered_df = finance_df[finance_df['month_year'] == selected_month]
        else:
            filtered_df = finance_df

        income = filtered_df[filtered_df['type'] == 'Income']['amount'].sum()
        expense = filtered_df[filtered_df['type'] == 'Expense']['amount'].sum()
        balance = income - expense

        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Total Income", f"₹{income:,.2f}")
        m_col2.metric("Total Expense", f"₹{expense:,.2f}")
        m_col3.metric("Net Balance", f"₹{balance:,.2f}")

        expense_df = filtered_df[filtered_df['type'] == 'Expense']
        if not expense_df.empty:
            st.plotly_chart(px.pie(expense_df, values='amount', names='category', title=f'Expenses by Category ({selected_month})'), use_container_width=True)

        st.subheader("Transaction History")
        display_cols = [col for col in filtered_df.columns if col != 'month_year']
        st.dataframe(filtered_df[display_cols].sort_values("f_date", ascending=False), use_container_width=True)

        del_id = st.selectbox("Delete Transaction (ID):", filtered_df["id"].unique())
        if st.button("❌ Delete Transaction"):
            delete_finance_record(del_id)
            st.rerun()
    else:
        st.info("No transactions logged yet.")

# --- PAGE 4: PORTFOLIO & GOALS ---
elif page == "Portfolio & Goals":
    st.title("📈 Portfolio & Financial Goals")
    
    tab1, tab2 = st.tabs(["💼 Portfolio Dashboard", "🎯 Financial Goals"])
    
    with tab1:
        st.subheader("Asset Allocation")
        portfolio_df = get_portfolio_data()
        if not portfolio_df.empty:
            total_invested = portfolio_df['invested_amount'].sum()
            total_current = portfolio_df['current_value'].sum()
            total_pl = total_current - total_invested
            pl_pct = (total_pl / total_invested * 100) if total_invested > 0 else 0
            
            p_col1, p_col2, p_col3 = st.columns(3)
            p_col1.metric("Total Invested", f"₹{total_invested:,.2f}")
            p_col2.metric("Current Value", f"₹{total_current:,.2f}", delta=f"₹{total_pl:,.2f} ({pl_pct:.2f}%)")
            p_col3.metric("Total Assets", len(portfolio_df))
            
            st.plotly_chart(px.pie(portfolio_df, values='current_value', names='asset_type', title='Portfolio by Asset Type'), use_container_width=True)
            
            st.dataframe(portfolio_df, use_container_width=True)
            
            del_p_id = st.selectbox("Delete Asset (ID):", portfolio_df["id"].unique(), key="del_p")
            if st.button("❌ Delete Asset"):
                delete_portfolio_asset(del_p_id)
                st.rerun()
                
            with st.expander("✏️ Edit Asset"):
                edit_p_id = st.selectbox("Select Asset to Edit:", portfolio_df["id"].unique(), format_func=lambda x: portfolio_df[portfolio_df["id"]==x]["asset_name"].iloc[0])
                if edit_p_id:
                    asset_to_edit = portfolio_df[portfolio_df["id"] == edit_p_id].iloc[0]
                    e_name = st.text_input("Asset Name", value=asset_to_edit["asset_name"], key="e_a_name")
                    
                    base_types = ["Stocks", "Crypto", "Bonds", "Real Estate", "Cash", "Other"]
                    existing_types = portfolio_df["asset_type"].unique().tolist() if not portfolio_df.empty else []
                    type_options = sorted(list(set(base_types + existing_types)))
                    default_idx = type_options.index(asset_to_edit["asset_type"]) if asset_to_edit["asset_type"] in type_options else 0
                    e_type_sel = st.selectbox("Asset Type", type_options + ["+ Add Custom Type"], index=default_idx, key="e_a_type_sel")
                    if e_type_sel == "+ Add Custom Type":
                        e_type = st.text_input("Enter Custom Asset Type", key="e_a_type_custom")
                    else:
                        e_type = e_type_sel
                        
                    e_inv = st.number_input("Invested Amount (₹)", min_value=0.0, value=float(asset_to_edit["invested_amount"]), key="e_a_inv")
                    e_cur = st.number_input("Current Value (₹)", min_value=0.0, value=float(asset_to_edit["current_value"]), key="e_a_cur")
                    if st.button("Save Changes", key="e_a_save"):
                        edit_portfolio_asset(edit_p_id, e_name, e_type, e_inv, e_cur)
                        st.rerun()
        else:
            st.info("No assets in portfolio yet.")
            
        with st.expander("➕ Add New Asset"):
            a_name = st.text_input("Asset Name (e.g. Apple Stock, Vanguard ETF)")
            
            base_types = ["Stocks", "Crypto", "Bonds", "Real Estate", "Cash", "Other"]
            existing_types = portfolio_df["asset_type"].unique().tolist() if not portfolio_df.empty else []
            type_options = sorted(list(set(base_types + existing_types)))
            a_type_sel = st.selectbox("Asset Type", type_options + ["+ Add Custom Type"])
            if a_type_sel == "+ Add Custom Type":
                a_type = st.text_input("Enter Custom Asset Type")
            else:
                a_type = a_type_sel
                
            a_inv = st.number_input("Invested Amount (₹)", min_value=0.0)
            a_cur = st.number_input("Current Value (₹)", min_value=0.0)
            if st.button("Add Asset"):
                add_portfolio_asset(a_name, a_type, a_inv, a_cur)
                st.rerun()
                
    with tab2:
        st.subheader("Savings & Milestones")
        goals_df = get_goals_data()
        
        if not goals_df.empty:
            for _, row in goals_df.iterrows():
                target_amt = max(0.01, float(row['target_amount']))
                progress = min(float(row['current_amount']) / target_amt, 1.0)
                
                g_type = row.get("goal_type", "Cash")
                if pd.isna(g_type) or g_type not in ["Cash", "Gram", "Size"]:
                    g_type = "Cash"
                    
                if g_type == "Cash":
                    prog_text = f"₹{row['current_amount']:,.2f} / ₹{row['target_amount']:,.2f} ({progress*100:.1f}%)"
                elif g_type == "Gram":
                    prog_text = f"{row['current_amount']:,.2f}g / {row['target_amount']:,.2f}g ({progress*100:.1f}%)"
                else:
                    prog_text = f"{row['current_amount']:,.2f} units / {row['target_amount']:,.2f} units ({progress*100:.1f}%)"
                    
                st.write(f"**{row['goal_name']}** ({g_type} | Target: {row['target_date']})")
                st.progress(progress, text=prog_text)
            
            st.divider()
            del_g_id = st.selectbox("Delete Goal (ID):", goals_df["id"].unique(), key="del_g")
            if st.button("❌ Delete Goal"):
                delete_financial_goal(del_g_id)
                st.rerun()
                
            with st.expander("✏️ Edit Goal"):
                edit_g_id = st.selectbox("Select Goal to Edit:", goals_df["id"].unique(), format_func=lambda x: goals_df[goals_df["id"]==x]["goal_name"].iloc[0])
                if edit_g_id:
                    goal_to_edit = goals_df[goals_df["id"] == edit_g_id].iloc[0]
                    eg_name = st.text_input("Goal Name", value=goal_to_edit["goal_name"], key="e_g_name")
                    
                    current_g_type = goal_to_edit.get("goal_type", "Cash")
                    if pd.isna(current_g_type) or current_g_type not in ["Cash", "Gram", "Size"]:
                        current_g_type = "Cash"
                        
                    eg_type = st.selectbox("Goal Type", ["Cash", "Gram", "Size"], index=["Cash", "Gram", "Size"].index(current_g_type), key="e_g_type")
                    
                    if eg_type == "Cash":
                        elbl_t, elbl_c = "Target Amount (₹)", "Currently Saved (₹)"
                    elif eg_type == "Gram":
                        elbl_t, elbl_c = "Target Weight (grams)", "Currently Saved (grams)"
                    else:
                        elbl_t, elbl_c = "Target Size (cents/acres)", "Currently Owned (cents/acres)"
                        
                    eg_target = st.number_input(elbl_t, min_value=0.01, value=float(max(0.01, goal_to_edit["target_amount"])), key="e_g_target")
                    eg_curr = st.number_input(elbl_c, min_value=0.0, value=float(goal_to_edit["current_amount"]), key="e_g_curr")
                    eg_date_val = pd.to_datetime(goal_to_edit["target_date"], errors='coerce')
                    eg_date = st.date_input("Target Date", value=eg_date_val.date() if pd.notnull(eg_date_val) else date.today(), key="e_g_date")
                    if st.button("Save Changes", key="e_g_save"):
                        edit_financial_goal(edit_g_id, eg_name, eg_type, eg_target, eg_curr, eg_date)
                        st.rerun()
        else:
            st.info("No financial goals set yet.")
            
        with st.expander("➕ Create New Goal"):
            g_name = st.text_input("Goal Name (e.g. House Downpayment, Gold Savings)")
            g_type = st.selectbox("Goal Type", ["Cash", "Gram", "Size"])
            
            if g_type == "Cash":
                lbl_t, lbl_c = "Target Amount (₹)", "Currently Saved (₹)"
            elif g_type == "Gram":
                lbl_t, lbl_c = "Target Weight (grams)", "Currently Saved (grams)"
            else:
                lbl_t, lbl_c = "Target Size (cents/acres)", "Currently Owned (cents/acres)"
                
            g_target = st.number_input(lbl_t, min_value=0.01, value=1.0)
            g_curr = st.number_input(lbl_c, min_value=0.0)
            g_date = st.date_input("Target Date")
            if st.button("Add Goal"):
                add_financial_goal(g_name, g_type, g_target, g_curr, g_date)
                st.rerun()

# --- PAGE 5: SHORT-TERM GOALS ---
elif page == "Short-Term Goals":
    st.title("🎯 Short-Term Goals Tracker")
    st.markdown("Track time-sensitive objectives like Interview Prep, Project Deadlines, or Certifications.")
    
    with st.expander("➕ Create New Short-Term Goal", expanded=False):
        st_g_name = st.text_input("Goal Name (e.g., Google Interview Prep)")
        st_g_date = st.date_input("Target Date")
        st_g_tasks = st.text_area("Checklist Tasks (Comma-separated)", placeholder="e.g., Arrays and Strings, System Design Concepts, Mock Interview")
        if st.button("Add Goal"):
            if st_g_name and st_g_tasks:
                add_short_term_goal(st_g_name, st_g_date, st_g_tasks)
                st.success("Goal added successfully!")
                st.rerun()
            else:
                st.warning("Please provide a name and at least one task.")

    goals_df = get_short_term_goals()
    
    if not goals_df.empty:
        with st.expander("✏️ Edit Existing Goal"):
            edit_stg_id = st.selectbox("Select Goal to Edit:", goals_df["id"].unique(), format_func=lambda x: goals_df[goals_df["id"]==x]["goal_name"].iloc[0], key="edit_stg_sel")
            if edit_stg_id:
                stg_to_edit = goals_df[goals_df["id"] == edit_stg_id].iloc[0]
                e_stg_name = st.text_input("Goal Name", value=stg_to_edit["goal_name"], key="e_stg_name")
                
                e_stg_date_val = pd.to_datetime(stg_to_edit["target_date"], errors='coerce')
                e_stg_date = st.date_input("Target Date", value=e_stg_date_val.date() if pd.notnull(e_stg_date_val) else date.today(), key="e_stg_date")
                
                e_stg_tasks = st.text_area("Checklist Tasks (Comma-separated)", value=str(stg_to_edit["tasks"]), key="e_stg_tasks", height=150)
                
                if st.button("Save Changes", key="e_stg_save"):
                    edit_short_term_goal(edit_stg_id, e_stg_name, e_stg_date, e_stg_tasks)
                    st.rerun()

        st.divider()

        for _, row in goals_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                col1.subheader(f"{row['goal_name']}")
                
                target_date = pd.to_datetime(row['target_date']).date()
                days_left = (target_date - date.today()).days
                
                if days_left < 0:
                    date_status = f"<span style='color:red;'>Overdue by {abs(days_left)} days</span>"
                elif days_left == 0:
                    date_status = "<span style='color:orange;'>Due Today!</span>"
                else:
                    date_status = f"<span style='color:lightgreen;'>{days_left} days left</span>"
                    
                col2.markdown(f"**Target:** {target_date}<br>{date_status}", unsafe_allow_html=True)
                
                all_tasks = [t.strip() for t in str(row['tasks']).split(",") if t.strip()]
                completed_tasks = [t.strip() for t in str(row.get('completed_tasks', '')).split(",") if t.strip()]
                
                if all_tasks:
                    valid_completed = [t for t in completed_tasks if t in all_tasks]
                    progress = min(len(valid_completed) / len(all_tasks), 1.0)
                    st.progress(progress, text=f"Progress: {len(valid_completed)}/{len(all_tasks)} Tasks Completed")
                    
                    st.markdown("**Tasks:**")
                    new_completed = []
                    for t in all_tasks:
                        if st.checkbox(t, value=(t in completed_tasks), key=f"stg_{row['id']}_{t}"):
                            new_completed.append(t)
                            
                    if set(new_completed) != set(completed_tasks):
                        update_short_term_goal_tasks(row['id'], ",".join(new_completed))
                        st.rerun()
                else:
                    st.info("No tasks added for this goal.")
                    
                if st.button("❌ Delete Goal", key=f"del_stg_{row['id']}"):
                    delete_short_term_goal(row['id'])
                    st.rerun()
    else:
        st.info("No short-term goals found. Add one above to get started!")

# --- PAGE 6: REMINDERS SCHEDULE ---
elif page == "Reminders Schedule":
    st.title("⏰ Reminders Schedule")
    st.markdown("Manage your daily ntfy.sh notification schedules here.")
    
    with st.expander("➕ Add New Reminder", expanded=True):
        r_time = st.time_input("Reminder Time")
        r_title = st.text_input("Title", placeholder="e.g. Study Time 📚")
        r_msg = st.text_area("Message", placeholder="e.g. Time to learn DSA and do job prep! 💻")
        
        if st.button("Add Reminder"):
            if r_title and r_msg:
                add_schedule(r_time.strftime("%H:%M"), r_msg, r_title)
                st.success("Reminder added!")
                st.rerun()
            else:
                st.warning("Please provide a title and message.")

    sched_df = get_schedules()
    if not sched_df.empty:
        st.subheader("Current Schedules")
        st.info("💡 Note: After adding or deleting schedules, click **▶️ Start Auto-Reminders** in the sidebar to apply changes!")
        
        for _, row in sched_df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                col1.markdown(f"**{row['reminder_time']}** - {row['title']}<br>_{row['message']}_", unsafe_allow_html=True)
                if col2.button("❌ Delete", key=f"del_sched_{row['id']}"):
                    delete_schedule(row['id'])
                    st.rerun()
    else:
        st.info("No reminders scheduled.")