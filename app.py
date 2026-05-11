import streamlit as st
import pandas as pd
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Postal Performance System", layout="wide")

# --- GLOBAL CONSTANTS ---
ANNUAL_CIRCLE_TARGET = 2450880  

# --- CUSTOM CSS ---
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] { background-color: #990000 !important; }
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] .stText { color: #000000 !important; }
        [data-testid="stSidebar"] div[data-baseweb="select"] > div {
            color: #000000 !important;
            background-color: #FFFFFF !important;
            border: 1px solid #000000;
        }
        [data-testid="stSidebar"] button {
            color: #FF0000 !important;
            background-color: #FFFFFF !important;
            border: 1px solid #000000;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# --- CONFIGURATION ---
FY_26_27_MONTHS = [
    "April 2026", "May 2026", "June 2026", "July 2026", "August 2026", "September 2026",
    "October 2026", "November 2026", "December 2026", "January 2027", "February 2027", "March 2027"
]
SCHEMES = ['MIS', 'PPFGP', 'SSA', 'RD', 'SBBAS', 'SBSGP', 'SCSS', 'TD', 'PRFTS', 'KVN', 'NSC8', 'MSSC']
AUTHORIZED_USERS = {"10032220": "Admin", "10213662": "Admin","10032111": "Admin","10185108": "Admin","44444444": "Viewer", "12345678": "Viewer"}

# --- DATA INITIALIZATION ---
if 'master_df' not in st.session_state:
    try:
        df = pd.read_csv("master_data.csv")
        df.columns = [str(c).strip() for c in df.columns]
        if 'SOL_ID_BO_ID' in df.columns:
            df['SOL_ID_BO_ID'] = df['SOL_ID_BO_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        st.session_state.master_df = df.drop_duplicates(subset=['SOL_ID_BO_ID'])
    except:
        st.session_state.master_df = pd.DataFrame(columns=['SOL_ID_BO_ID', 'Office_ID', 'Office_Name', 'Division', 'Sub_Division', 'office_type_code', 'net target'])

if 'monthly_df' not in st.session_state:
    if os.path.exists("monthly_data.csv"):
        try:
            m_df = pd.read_csv("monthly_data.csv")
            m_df['SOL_ID_BO_ID'] = m_df['SOL_ID_BO_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            st.session_state.monthly_df = m_df
        except:
            st.session_state.monthly_df = None
    else:
        st.session_state.monthly_df = None

# --- AUTH LOGIC ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("POSB Haryana Dashboard")
    emp_id_in = st.text_input("Enter 8-Digit Employee ID", max_chars=8)
    if st.button("Login"):
        if emp_id_in in AUTHORIZED_USERS:
            st.session_state.logged_in, st.session_state.user_role, st.session_state.emp_id = True, AUTHORIZED_USERS[emp_id_in], emp_id_in
            st.rerun()
        else: st.error("Unauthorized Access")
else:
    # --- SIDEBAR ---
    st.sidebar.title("👤 Haryana Postal Circle")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    is_admin = (st.session_state.user_role == "Admin")
    choice = st.sidebar.selectbox("Navigate To", ["📊 Dashboard", "⚙️ Data Management"] if is_admin else ["📊 Dashboard"])

    st.sidebar.divider()
    st.sidebar.subheader("📍 Selection Filters")
    view_month = st.sidebar.selectbox("Reporting Month", FY_26_27_MONTHS)
    
    div_list = sorted(st.session_state.master_df['Division'].dropna().unique().tolist())
    sel_div = st.sidebar.selectbox("Division", ["All"] + div_list)

    m_temp = st.session_state.master_df
    if sel_div != "All": m_temp = m_temp[m_temp['Division'] == sel_div]
    
    sub_div_list = sorted(m_temp['Sub_Division'].dropna().unique().tolist())
    sel_sub_div = st.sidebar.selectbox("Sub-Division", ["All"] + sub_div_list)

    type_list = sorted(st.session_state.master_df['office_type_code'].dropna().unique().tolist())
    sel_type = st.sidebar.selectbox("Office Type", ["All"] + type_list)

    # --- DATA MANAGEMENT ---
    if choice == "⚙️ Data Management" and is_admin:
        st.title("⚙️ Data Management")
        t1, t2, t3 = st.tabs(["📤 Master Upload", "📈 Monthly Performance", "🗑️ Delete Data"])
        
        with t1:
            m_file = st.file_uploader("Upload Master CSV", type="csv")
            if st.button("Update Master Data"):
                if m_file:
                    df = pd.read_csv(m_file)
                    df = df.drop_duplicates(subset=['SOL_ID_BO_ID'])
                    df.to_csv("master_data.csv", index=False)
                    st.session_state.master_df = df
                    st.success("Master Saved & Deduplicated!")

        with t2:
            st.subheader("Upload Performance")
            up_month = st.selectbox("Select Month for Upload", FY_26_27_MONTHS)
            p_file = st.file_uploader(f"Choose File for {up_month}", type=["csv", "xlsx"])
            if st.button("Save Data"):
                if p_file:
                    df_new = pd.read_csv(p_file) if p_file.name.endswith('.csv') else pd.read_excel(p_file)
                    df_new.columns = [str(c).strip() for c in df_new.columns]
                    if 'SOL ID / BOCODE' in df_new.columns: 
                        df_new.rename(columns={'SOL ID / BOCODE': 'SOL_ID_BO_ID'}, inplace=True)
                    
                    df_new['SOL_ID_BO_ID'] = df_new['SOL_ID_BO_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_new['Month_Year'] = up_month
                    
                    df_old = st.session_state.monthly_df
                    if df_old is not None and not df_old.empty:
                        df_old = df_old[df_old['Month_Year'] != up_month]
                        df_final = pd.concat([df_old, df_new], ignore_index=True)
                    else:
                        df_final = df_new
                        
                    df_final.to_csv("monthly_data.csv", index=False)
                    st.session_state.monthly_df = df_final
                    st.success(f"Data for {up_month} updated!")
                    st.rerun()
        
        with t3:
            if st.session_state.monthly_df is not None and not st.session_state.monthly_df.empty:
                existing_months = st.session_state.monthly_df['Month_Year'].unique()
                del_month = st.selectbox("Select Month to Delete", existing_months)
                if st.button("Confirm Delete"):
                    df_remaining = st.session_state.monthly_df[st.session_state.monthly_df['Month_Year'] != del_month]
                    df_remaining.to_csv("monthly_data.csv", index=False)
                    st.session_state.monthly_df = df_remaining
                    st.warning(f"Data for {del_month} deleted.")
                    st.rerun()

    # --- DASHBOARD ---
    elif choice == "📊 Dashboard":
        st.title(f"POSB Performance Analysis: {view_month}")
        
        f_df = st.session_state.master_df.copy().drop_duplicates(subset=['SOL_ID_BO_ID'])
        
        if sel_div != "All": f_df = f_df[f_df['Division'] == sel_div]
        if sel_sub_div != "All": f_df = f_df[f_df['Sub_Division'] == sel_sub_div]
        if sel_type != "All": f_df = f_df[f_df['office_type_code'] == sel_type]

        has_monthly_data = (st.session_state.monthly_df is not None and 
                            not st.session_state.monthly_df.empty and 
                            view_month in st.session_state.monthly_df['Month_Year'].values)

        if has_monthly_data:
            all_m = st.session_state.monthly_df.copy().drop_duplicates()
            found_s = [c for c in SCHEMES if c in all_m.columns]
            all_m[found_s] = all_m[found_s].apply(pd.to_numeric, errors='coerce').fillna(0)
            
            all_m_grouped = all_m.groupby(['SOL_ID_BO_ID', 'Month_Year'])[found_s].sum().reset_index()
            all_m_grouped['Row_Total'] = all_m_grouped[found_s].sum(axis=1)

            curr_idx = FY_26_27_MONTHS.index(view_month)
            prev_months = FY_26_27_MONTHS[:curr_idx]

            if prev_months:
                prev_perf = all_m_grouped[all_m_grouped['Month_Year'].isin(prev_months)].groupby('SOL_ID_BO_ID')['Row_Total'].sum().reset_index()
                prev_perf.rename(columns={'Row_Total': 'Prev_Months_Total'}, inplace=True)
                total_achieved_before = prev_perf['Prev_Months_Total'].sum()
            else:
                prev_perf = pd.DataFrame(columns=['SOL_ID_BO_ID', 'Prev_Months_Total'])
                total_achieved_before = 0

            curr_m_perf = all_m_grouped[all_m_grouped['Month_Year'] == view_month].groupby('SOL_ID_BO_ID')['Row_Total'].sum().reset_index()
            curr_m_perf.rename(columns={'Row_Total': 'Curr_Month_Opened'}, inplace=True)

            final_df = pd.merge(f_df, prev_perf, on='SOL_ID_BO_ID', how='left').fillna(0)
            final_df = pd.merge(final_df, curr_m_perf, on='SOL_ID_BO_ID', how='left').fillna(0)
            
            final_df['Curr_Month_Opened'] = final_df['Curr_Month_Opened'].astype(int)
            final_df['net target'] = final_df['net target'].astype(int)
            final_df['Prev_Months_Total'] = final_df['Prev_Months_Total'].astype(int)
            final_df['Target_Left_Closing'] = (final_df['net target'] - final_df['Prev_Months_Total'] - final_df['Curr_Month_Opened']).astype(int)

            # --- DYNAMIC SLIDER & REAL-TIME SYNC LOGIC ---
            max_val = int(final_df['Curr_Month_Opened'].max())
            if max_val > 0:
                st.sidebar.divider()
                st.sidebar.subheader("Filter by Accounts Opened")
                
                # Initialize state for synchronization
                if "threshold_val" not in st.session_state:
                    st.session_state.threshold_val = max_val

                # Callback functions for bidirectional update
                def sync_num_to_slider():
                    st.session_state.threshold_val = st.session_state.num_in

                def sync_slider_to_num():
                    st.session_state.threshold_val = st.session_state.slider_in

                # 1. Manual Number Input
                st.sidebar.number_input(
                    "Enter manual count:", 
                    min_value=0, 
                    max_value=max_val, 
                    value=st.session_state.threshold_val,
                    key="num_in",
                    on_change=sync_num_to_slider
                )

                # 2. Slider Control
                st.sidebar.slider(
                    "Slide to adjust range:", 
                    0, 
                    max_val, 
                    value=st.session_state.threshold_val,
                    key="slider_in",
                    on_change=sync_slider_to_num
                )

                # Apply the filter based on the synchronized session state
                threshold = st.session_state.threshold_val
                final_df = final_df[final_df['Curr_Month_Opened'] <= threshold]

            total_curr = int(final_df['Curr_Month_Opened'].sum())
            rem_global = int(ANNUAL_CIRCLE_TARGET - (total_achieved_before + total_curr))

            c1, c2, c3 = st.columns(3)
            c1.metric("Annual Circle Target", f"{ANNUAL_CIRCLE_TARGET:,.0f}")
            c2.metric(f"Filtered Total ({view_month})", f"{total_curr:,.0f}")
            c3.metric("Remaining Circle Target", f"{rem_global:,.0f}")

            st.divider()
            st.subheader(f"📊 Office wise POSB Performance")
            
            display_map = {
                'SOL_ID_BO_ID': 'ID',
                'Office_ID': 'Office ID',
                'Office_Name': 'Office Name',
                'Sub_Division': 'Sub-Division',
                'Division': 'Division',
                'net target': 'Annual Target',
                'Prev_Months_Total': 'Achieved (Before)',
                'Curr_Month_Opened': f'Opened in {view_month.split()[0]}',
                'Target_Left_Closing': 'Remaining Target'
            }
            
            available_cols = [col for col in display_map.keys() if col in final_df.columns]
            table_data = final_df[available_cols].rename(columns=display_map)

            st.dataframe(
                table_data.style.format(precision=0, thousands=""),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(f"Data not present for the month of {view_month}.")
            st.info("Please upload performance data for this month in the 'Data Management' tab.")