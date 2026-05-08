import streamlit as st
import pandas as pd
import base64
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import plotly.express as px

# --- CONFIGURATION ---
TOTAL_DAYS = 365


# def set_bg_image(image_path):
#     try:
#         with open(image_path, "rb") as image_file:
#             encoded_string = base64.b64encode(image_file.read()).decode()
#         st.markdown(
#             f"""
#             <style>
#             .stApp {{
#                 background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("data:image/jpeg;base64,{encoded_string}");
#                 background-size: cover;
#                 background-position: center;
#                 background-attachment: fixed;
#             }}
#             </style>
#             """,
#             unsafe_allow_html=True
#         )
#     except FileNotFoundError:
#         st.warning(f"Background image not found: {image_path}")
# 
# # Set the Naruto Background
# set_bg_image("naruto.jpg")

# Set gradient background
st.markdown(
    """
    <style>
    .stApp {
        background-image: linear-gradient(to right, #141e30, #243b55);
    }
    </style>
    """,
    unsafe_allow_html=True
)

@st.cache_resource
def get_gsheets_client():
    creds_dict = st.secrets["connections"]["gsheets"].to_dict()

    if "private_key" in creds_dict:
        # Clean the key: remove literal \n strings and extra whitespace
        cleaned_key = creds_dict["private_key"].replace("\\n", "\n").strip()
        creds_dict["private_key"] = cleaned_key

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)


# Initialize Client and Spreadsheet
try:
    gc = get_gsheets_client()
    # Replace 'Your Sheet Name' with the actual filename of your Google Sheet
    sh = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    st.sidebar.success("✅ Cloud Sync Active")
except Exception as e:
    st.error(f"Connection Failed: {e}")
    st.stop()


# --- DATA HELPERS ---
@st.cache_data(ttl=600)
def get_worksheet_data(name):
    try:
        ws = sh.worksheet(name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except:
        if name == "Logs":
            return pd.DataFrame(columns=["day_num", "log_date", "tasks_completed", "completed_tasks", "weight", "notes"])
        elif name == "Finance":
            return pd.DataFrame(columns=["id", "date", "type", "category", "amount", "notes"])
        elif name == "Portfolio":
            return pd.DataFrame(columns=["id", "asset_name", "asset_type", "invested_amount", "current_value"])
        elif name == "Goals":
            return pd.DataFrame(columns=["id", "goal_name", "goal_type", "target_amount", "current_amount", "target_date"])
        elif name == "ShortTermGoals":
            return pd.DataFrame(columns=["id", "goal_name", "target_date", "tasks", "completed_tasks"])
        return pd.DataFrame({"id": [1, 2, 3], "task_name": ["10k Steps Walk", "Study DSA", "3L Water"]})


def sync_to_cloud(df, name):
    try:
        ws = sh.worksheet(name)
    except gspread.WorksheetNotFound:
        # Create the worksheet if it doesn't exist yet
        ws = sh.add_worksheet(title=name, rows="1000", cols="20")

    ws.clear()
    
    # Convert dataframe to string to prevent numpy int64/float64 JSON serialization errors
    data_to_sync = [df.columns.values.tolist()] + df.astype(str).fillna("").values.tolist()
    
    try:
        ws.update(values=data_to_sync, range_name="A1")
    except TypeError:
        # Fallback for older gspread versions
        ws.update(data_to_sync)
    
    st.cache_data.clear()


# --- ACTION FUNCTIONS ---
def add_task(name):
    df = get_worksheet_data("Tasks")
    new_id = int(df["id"].max() + 1) if not df.empty else 1
    new_row = pd.DataFrame([{"id": new_id, "task_name": name}])
    df = pd.concat([df, new_row], ignore_index=True)
    sync_to_cloud(df, "Tasks")


def delete_task(t_id):
    df = get_worksheet_data("Tasks")
    df = df[df["id"].astype(str) != str(t_id)]
    sync_to_cloud(df, "Tasks")


def save_log(day, log_date, score, completed_tasks, weight, note):
    df = get_worksheet_data("Logs")
    if "completed_tasks" not in df.columns:
        df["completed_tasks"] = ""
    df = df[df["day_num"].astype(str) != str(day)]
    new_log = pd.DataFrame([{
        "day_num": int(day),
        "log_date": str(log_date),
        "tasks_completed": int(score),
        "completed_tasks": ", ".join(completed_tasks),
        "weight": float(weight),
        "notes": str(note)
    }])
    df = pd.concat([df, new_log], ignore_index=True)
    sync_to_cloud(df, "Logs")


def delete_log_entry(day_n):
    df = get_worksheet_data("Logs")
    df = df[df["day_num"].astype(str) != str(day_n)]
    sync_to_cloud(df, "Logs")


def add_finance_record(f_date, f_type, category, amount, notes):
    df = get_worksheet_data("Finance")
    new_id = int(df["id"].max() + 1) if not df.empty else 1
    new_row = pd.DataFrame([{
        "id": new_id,
        "date": str(f_date),
        "type": str(f_type),
        "category": str(category),
        "amount": float(amount),
        "notes": str(notes)
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    sync_to_cloud(df, "Finance")

def delete_finance_record(f_id):
    df = get_worksheet_data("Finance")
    df = df[df["id"].astype(str) != str(f_id)]
    sync_to_cloud(df, "Finance")

def add_portfolio_asset(asset_name, asset_type, invested_amount, current_value):
    df = get_worksheet_data("Portfolio")
    new_id = int(df["id"].max() + 1) if not df.empty else 1
    new_row = pd.DataFrame([{"id": new_id, "asset_name": str(asset_name), "asset_type": str(asset_type), "invested_amount": float(invested_amount), "current_value": float(current_value)}])
    df = pd.concat([df, new_row], ignore_index=True)
    sync_to_cloud(df, "Portfolio")

def delete_portfolio_asset(p_id):
    df = get_worksheet_data("Portfolio")
    df = df[df["id"].astype(str) != str(p_id)]
    sync_to_cloud(df, "Portfolio")

def add_financial_goal(goal_name, goal_type, target_amount, current_amount, target_date):
    df = get_worksheet_data("Goals")
    if "goal_type" not in df.columns:
        df["goal_type"] = "Cash"
    new_id = int(df["id"].max() + 1) if not df.empty else 1
    new_row = pd.DataFrame([{"id": new_id, "goal_name": str(goal_name), "goal_type": str(goal_type), "target_amount": float(target_amount), "current_amount": float(current_amount), "target_date": str(target_date)}])
    df = pd.concat([df, new_row], ignore_index=True)
    sync_to_cloud(df, "Goals")

def delete_financial_goal(g_id):
    df = get_worksheet_data("Goals")
    df = df[df["id"].astype(str) != str(g_id)]
    sync_to_cloud(df, "Goals")

def edit_portfolio_asset(p_id, asset_name, asset_type, invested_amount, current_value):
    df = get_worksheet_data("Portfolio")
    idx = df.index[df['id'].astype(str) == str(p_id)].tolist()
    if idx:
        df.at[idx[0], 'asset_name'] = str(asset_name)
        df.at[idx[0], 'asset_type'] = str(asset_type)
        df.at[idx[0], 'invested_amount'] = float(invested_amount)
        df.at[idx[0], 'current_value'] = float(current_value)
        sync_to_cloud(df, "Portfolio")

def edit_financial_goal(g_id, goal_name, goal_type, target_amount, current_amount, target_date):
    df = get_worksheet_data("Goals")
    if "goal_type" not in df.columns:
        df["goal_type"] = "Cash"
    idx = df.index[df['id'].astype(str) == str(g_id)].tolist()
    if idx:
        df.at[idx[0], 'goal_name'] = str(goal_name)
        df.at[idx[0], 'goal_type'] = str(goal_type)
        df.at[idx[0], 'target_amount'] = float(target_amount)
        df.at[idx[0], 'current_amount'] = float(current_amount)
        df.at[idx[0], 'target_date'] = str(target_date)
        sync_to_cloud(df, "Goals")

def add_short_term_goal(goal_name, target_date, tasks):
    df = get_worksheet_data("ShortTermGoals")
    new_id = int(df["id"].max() + 1) if not df.empty else 1
    new_row = pd.DataFrame([{"id": new_id, "goal_name": str(goal_name), "target_date": str(target_date), "tasks": str(tasks), "completed_tasks": ""}])
    df = pd.concat([df, new_row], ignore_index=True)
    sync_to_cloud(df, "ShortTermGoals")

def delete_short_term_goal(g_id):
    df = get_worksheet_data("ShortTermGoals")
    df = df[df["id"].astype(str) != str(g_id)]
    sync_to_cloud(df, "ShortTermGoals")

def update_short_term_goal_tasks(g_id, completed_tasks):
    df = get_worksheet_data("ShortTermGoals")
    idx = df.index[df['id'].astype(str) == str(g_id)].tolist()
    if idx:
        df.at[idx[0], 'completed_tasks'] = str(completed_tasks)
        sync_to_cloud(df, "ShortTermGoals")

def edit_short_term_goal(g_id, goal_name, target_date, tasks):
    df = get_worksheet_data("ShortTermGoals")
    idx = df.index[df['id'].astype(str) == str(g_id)].tolist()
    if idx:
        df.at[idx[0], 'goal_name'] = str(goal_name)
        df.at[idx[0], 'target_date'] = str(target_date)
        df.at[idx[0], 'tasks'] = str(tasks)
        sync_to_cloud(df, "ShortTermGoals")

# --- UI LOGIC ---
st.sidebar.title("🗓️ Control Center")
challenge_start_date = st.sidebar.date_input("Challenge Start Date", value=date(2026, 5, 7))
selected_date = st.sidebar.date_input("Select Date", value=date.today())
page = st.sidebar.radio("View", ["Daily Log", "Analytics & History", "Finance Tracker", "Portfolio & Goals", "Short-Term Goals"])

# Manage Checklist Logic
st.sidebar.divider()
st.sidebar.subheader("⚙️ Manage Checklist")
new_task_input = st.sidebar.text_input("New task name...")
if st.sidebar.button("Add to Checklist"):
    if new_task_input:
        add_task(new_task_input)
        st.rerun()

tasks_df = get_worksheet_data("Tasks")
for _, row in tasks_df.iterrows():
    col_t, col_b = st.sidebar.columns([4, 1])
    col_t.write(f"• {row['task_name']}")
    if col_b.button("🗑️", key=f"del_t_{row['id']}"):
        delete_task(row['id'])
        st.rerun()

active_day_num = (selected_date - challenge_start_date).days + 1

# --- PAGE 1: DAILY LOG ---
if page == "Daily Log":
    st.title(f"🚀 Day {active_day_num} of {TOTAL_DAYS}")

    logs_df = get_worksheet_data("Logs")
    existing_entry = logs_df[logs_df['day_num'].astype(str) == str(active_day_num)]
    has_data = not existing_entry.empty

    val_w = float(existing_entry["weight"].iloc[0]) if has_data else 92.0
    val_note = str(existing_entry["notes"].iloc[0]) if has_data else ""
    
    if has_data and "completed_tasks" in existing_entry.columns:
        val_completed_tasks = [t.strip() for t in str(existing_entry["completed_tasks"].iloc[0]).split(",") if t.strip()]
    else:
        val_completed_tasks = []

    col1, col2 = st.columns(2)
    with col1:
        current_w = st.number_input("Current Weight (kg)", value=val_w, step=0.1)
    with col2:
        st.metric("Goal: 82.0 kg", f"{current_w} kg", delta=f"{82.0 - current_w:.1f} kg")

    st.subheader("Daily Checklist")
    task_list = tasks_df["task_name"].tolist()
    checked = [st.checkbox(t, value=(t in val_completed_tasks), key=f"c_{t}_{active_day_num}") for t in task_list]
    score = sum(checked)
    completed_task_names = [t for t, c in zip(task_list, checked) if c]

    user_note = st.text_area("Observations:", value=val_note)

    if st.button("Save to Cloud"):
        save_log(active_day_num, selected_date, score, completed_task_names, current_w, user_note)
        st.balloons()
        st.success(f"Day {active_day_num} Saved!")

# --- PAGE 2: ANALYTICS ---
elif page == "Analytics & History":
    st.title("📊 Cloud Analytics")
    hist_df = get_worksheet_data("Logs")

    if not hist_df.empty:
        hist_df['day_num'] = pd.to_numeric(hist_df['day_num'])
        hist_df = hist_df.sort_values("day_num")

        st.plotly_chart(px.line(hist_df, x="day_num", y="tasks_completed", title="Activity Trend", markers=True))

        fig_w = px.line(hist_df, x="day_num", y="weight", title="Weight Journey", markers=True)
        fig_w.add_hline(y=82.0, line_dash="dash", line_color="green")
        st.plotly_chart(fig_w)

        st.divider()
        st.subheader("History Table")
        st.dataframe(hist_df.sort_values("day_num", ascending=False), use_container_width=True)

        log_to_delete = st.selectbox("Delete Entry for Day:", hist_df["day_num"].unique())
        if st.button("❌ Permanent Delete"):
            delete_log_entry(log_to_delete)
            st.rerun()
    else:
        st.warning("No data found in Google Sheets.")

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

    finance_df = get_worksheet_data("Finance")

    if not finance_df.empty:
        finance_df['amount'] = pd.to_numeric(finance_df['amount'])

        finance_df['date'] = pd.to_datetime(finance_df['date'], errors='coerce')
        finance_df['month_year'] = finance_df['date'].dt.strftime('%Y-%m')

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
        st.dataframe(filtered_df[display_cols].sort_values("date", ascending=False), use_container_width=True)

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
        portfolio_df = get_worksheet_data("Portfolio")
        if not portfolio_df.empty:
            portfolio_df['invested_amount'] = pd.to_numeric(portfolio_df['invested_amount'])
            portfolio_df['current_value'] = pd.to_numeric(portfolio_df['current_value'])
            
            total_invested = portfolio_df['invested_amount'].sum()
            total_current = portfolio_df['current_value'].sum()
            total_pl = total_current - total_invested
            pl_pct = (total_pl / total_invested * 100) if total_invested > 0 else 0
            
            with st.container(border=True):
                p_col1, p_col2, p_col3 = st.columns(3)
                p_col1.metric("Total Invested", f"₹{total_invested:,.2f}")
                p_col2.metric("Current Value", f"₹{total_current:,.2f}", delta=f"₹{total_pl:,.2f} ({pl_pct:.2f}%)")
                p_col3.metric("Total Assets", len(portfolio_df))
            
            with st.container(border=True):
                st.plotly_chart(px.pie(portfolio_df, values='current_value', names='asset_type', title='Portfolio by Asset Type', hole=0.4), use_container_width=True)
            
            with st.container(border=True):
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
        goals_df = get_worksheet_data("Goals")
        
        if not goals_df.empty:
            goals_df['target_amount'] = pd.to_numeric(goals_df['target_amount'])
            goals_df['current_amount'] = pd.to_numeric(goals_df['current_amount'])
            
            with st.container(border=True):
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

    goals_df = get_worksheet_data("ShortTermGoals")
    
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