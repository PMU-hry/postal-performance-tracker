import streamlit as st
import pandas as pd
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Postal Performance System", layout="wide")

# --- MOCK USER DATABASE ---
# Replace these with your actual 8-digit Employee IDs
AUTHORIZED_USERS = {
    "11111111": "Admin",
    "22222222": "Admin",
    "33333333": "Viewer",
    "44444444": "Viewer"
}

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'emp_id' not in st.session_state:
    st.session_state.emp_id = None

# 1. Initialize Master Data Database
if 'master_df' not in st.session_state:
    try:
        df = pd.read_csv("master_data.csv")
        df.columns = [str(c).strip() for c in df.columns]
        if 'SOL_ID_BO_ID' in df.columns:
            df['SOL_ID_BO_ID'] = df['SOL_ID_BO_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        st.session_state.master_df = df
    except:
        # Added 'Office ID' to the default fallback list
        st.session_state.master_df = pd.DataFrame(columns=['Office ID', 'SOL_ID_BO_ID', 'Office_Name', 'Division', 'Sub_Division', 'office_type_code', 'net target'])

# 2. Initialize Permanent Monthly Data Database
if 'monthly_df' not in st.session_state:
    if os.path.exists("monthly_data.csv"):
        try:
            m_df = pd.read_csv("monthly_data.csv")
            # Ensure SOL_ID stays as a string to match master data
            if 'SOL_ID_BO_ID' in m_df.columns:
                m_df['SOL_ID_BO_ID'] = m_df['SOL_ID_BO_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            st.session_state.monthly_df = m_df
        except:
            st.session_state.monthly_df = None
    else:
        st.session_state.monthly_df = None

# --- LOGIN PAGE FUNCTION ---
def login_page():
    st.title(" POSB Haryana Dashboard")
    st.markdown("### Please Log In")
    
    with st.container():
        emp_id_input = st.text_input("Enter 8-Digit Employee ID", max_chars=8)
        
        if st.button("Login"):
            if len(emp_id_input) == 8 and emp_id_input.isdigit():
                if emp_id_input in AUTHORIZED_USERS:
                    st.session_state.logged_in = True
                    st.session_state.emp_id = emp_id_input
                    st.session_state.user_role = AUTHORIZED_USERS[emp_id_input]
                    st.rerun()
                else:
                    st.error("Access Denied: Employee ID not found in authorized user list.")
            else:
                st.warning("Invalid Format: Please enter a valid 8-digit numeric ID.")

# --- LOGOUT FUNCTION ---
def logout():
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.emp_id = None

# --- MAIN APPLICATION LOGIC ---
if not st.session_state.logged_in:
    login_page()
else:
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.title("👤 Portal")
    st.sidebar.write(f"**Logged in as:** {st.session_state.emp_id}")
    st.sidebar.write(f"**Role:** {st.session_state.user_role}")
    st.sidebar.button("Logout", on_click=logout)
    
    is_admin = (st.session_state.user_role == "Admin")
    
    menu = ["📊 Dashboard"]
    if is_admin:
        menu.append("⚙️ Data Management")
    
    choice = st.sidebar.selectbox("Navigate To", menu)

    # --- GLOBAL FILTERS ---
    st.sidebar.divider()
    st.sidebar.header("📍 Data Filters")

    df_to_filter = st.session_state.master_df

    # 1. Division Filter
    div_list = sorted(df_to_filter['Division'].dropna().unique().tolist())
    sel_div = st.sidebar.selectbox("Select Division", ["All"] + div_list)

    # 2. Sub-Division Filter (Cascading)
    if sel_div != "All":
        sub_div_list = sorted(df_to_filter[df_to_filter['Division'] == sel_div]['Sub_Division'].dropna().unique().tolist())
    else:
        sub_div_list = sorted(df_to_filter['Sub_Division'].dropna().unique().tolist())
    sel_sub_div = st.sidebar.selectbox("Select Sub-Division", ["All"] + sub_div_list)

    # 3. Office Type Filter (Cascading)
    temp_df = df_to_filter.copy()
    if sel_div != "All": 
        temp_df = temp_df[temp_df['Division'] == sel_div]
    if sel_sub_div != "All": 
        temp_df = temp_df[temp_df['Sub_Division'] == sel_sub_div]
        
    office_type_list = sorted(temp_df['office_type_code'].astype(str).dropna().unique().tolist())
    sel_office_type = st.sidebar.selectbox("Select Office Type", ["All"] + office_type_list)

    # Apply All Filters for display
    display_df = st.session_state.master_df.copy()
    if sel_div != "All":
        display_df = display_df[display_df['Division'] == sel_div]
    if sel_sub_div != "All":
        display_df = display_df[display_df['Sub_Division'] == sel_sub_div]
    if sel_office_type != "All":
        display_df = display_df[display_df['office_type_code'].astype(str) == sel_office_type]

    # ==========================================
    # ⚙️ DATA MANAGEMENT (ADMIN ONLY)
    # ==========================================
    if choice == "⚙️ Data Management" and is_admin:
        st.title("⚙️ Administrative Data Management")
        
        tab_master, tab_monthly, tab_edit = st.tabs(["📤 Master Data", "📈 Monthly Data Upload", "📝 Modify / Delete"])
        
        # 1. Master Data Upload
        with tab_master:
            st.subheader("Upload Master Office & Target Records")
            up_file = st.file_uploader("Upload Master CSV (Replaces Current)", type=["csv"], key="master_upload")
            if st.button("Overwrite Master Data"):
                if up_file:
                    try:
                        new_df = pd.read_csv(up_file)
                        if 'SOL_ID_BO_ID' in new_df.columns:
                            new_df['SOL_ID_BO_ID'] = new_df['SOL_ID_BO_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                        st.session_state.master_df = new_df
                        # Permanently save master data
                        new_df.to_csv("master_data.csv", index=False)
                        st.success("Master data updated and saved permanently!")
                        st.rerun()
                    except PermissionError:
                        st.error("⚠️ **Upload failed:** Please completely close `master_data.csv` in Excel before uploading.")
                else:
                    st.warning("Please upload a file first.")

        # 2. Monthly Performance Upload
        with tab_monthly:
            st.subheader("Manage Monthly Performance Data")
            
            # Show current status
            if st.session_state.monthly_df is not None:
                st.success("✅ Monthly data is currently loaded and visible to viewers.")
                if st.button("🗑️ Delete Current Monthly Data", type="primary"):
                    if os.path.exists("monthly_data.csv"):
                        try:
                            os.remove("monthly_data.csv")
                            st.session_state.monthly_df = None
                            st.warning("Monthly data has been deleted.")
                            st.rerun()
                        except PermissionError:
                            st.error("⚠️ **Delete failed:** Please close `monthly_data.csv` in Microsoft Excel, then try again.")
                st.divider()
            
            st.info("Uploading new data here will overwrite the current monthly data for all viewers.")
            monthly_file = st.file_uploader("Upload Monthly Data", type=["csv", "xlsx"], key="monthly_upload")
            
            if st.button("Upload and Save Dashboard Data"):
                if monthly_file:
                    try:
                        if monthly_file.name.endswith('.csv'):
                            m_df = pd.read_csv(monthly_file)
                        else:
                            m_df = pd.read_excel(monthly_file)
                            
                        # Standardization
                        m_df.columns = [str(c).strip() for c in m_df.columns]
                        if 'SOL ID / BOCODE' in m_df.columns:
                            m_df = m_df.rename(columns={'SOL ID / BOCODE': 'SOL_ID_BO_ID'})
                        m_df['SOL_ID_BO_ID'] = m_df['SOL_ID_BO_ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                        
                        # Save to session and to disk permanently
                        st.session_state.monthly_df = m_df
                        m_df.to_csv("monthly_data.csv", index=False)
                        
                        st.success("Monthly Dashboard Data saved permanently! Viewers can now see the results.")
                        st.rerun()
                    except PermissionError:
                        st.error("⚠️ **Upload failed:** The system cannot save the data because `monthly_data.csv` is currently open. Please close Excel and try again.")
                    except Exception as e:
                        st.error(f"Error processing file: {e}")
                else:
                    st.warning("Please upload a monthly performance file first.")

        # 3. Edit / Delete Records
        with tab_edit:
            st.subheader("Modify or Delete Existing Master Records")
            search_id = st.text_input("Search SOL_ID to Edit or Delete")
            
            if search_id:
                res = st.session_state.master_df[st.session_state.master_df['SOL_ID_BO_ID'] == search_id]
                if not res.empty:
                    idx = res.index[0]
                    col1, col2 = st.columns(2)
                    new_name = col1.text_input("Office Name", res.iloc[0]['Office_Name'])
                    new_target = col2.number_input("Net Target", value=float(res.iloc[0]['net target']))
                    
                    c1, c2 = st.columns(2)
                    if c1.button("✅ Update Record"):
                        st.session_state.master_df.at[idx, 'Office_Name'] = new_name
                        st.session_state.master_df.at[idx, 'net target'] = new_target
                        try:
                            st.session_state.master_df.to_csv("master_data.csv", index=False)
                            st.success("Record Updated!")
                            st.rerun()
                        except PermissionError:
                            st.error("⚠️ Please close `master_data.csv` in Excel so the system can save your changes.")
                    
                    if c2.button("🗑️ Delete Office", type="primary"):
                        st.session_state.master_df = st.session_state.master_df.drop(idx)
                        try:
                            st.session_state.master_df.to_csv("master_data.csv", index=False)
                            st.warning("Office Record Deleted!")
                            st.rerun()
                        except PermissionError:
                            st.error("⚠️ Please close `master_data.csv` in Excel so the system can save your changes.")
                else:
                    st.error("SOL ID not found in the Master Data.")

    # ==========================================
    # 📊 DASHBOARD (VIEWER & ADMIN)
    # ==========================================
    elif choice == "📊 Dashboard":
        st.title("POSB Haryana Dashboard")

        # Helper function to dynamically append whatever columns we want
        def get_clean_table_columns(df_to_clean, performance_cols=[]):
            display_cols = []
            
            # Find Office ID gracefully
            for c in df_to_clean.columns:
                if str(c).strip().lower() in ['office id', 'office_id']:
                    display_cols.append(c)
                    break
            
            # Core Office Details
            core_cols = ['SOL_ID_BO_ID', 'Office_Name', 'Sub_Division', 'Division', 'office_type_code']
            for c in core_cols:
                if c in df_to_clean.columns:
                    display_cols.append(c)
            
            # Add specific account breakdown & total columns
            for c in performance_cols:
                if c in df_to_clean.columns:
                    display_cols.append(c)
                    
            # Rename mapping for clean display
            rename_map = {
                'SOL_ID_BO_ID': 'Office ID (SOL/BO)',
                'Office_Name': 'Office Name',
                'Sub_Division': 'Sub-Division',
                'Division': 'Division',
                'office_type_code': 'Office Type',
                'Total_Monthly_Opened': 'Total Accounts Opened'
            }
            
            for c in display_cols:
                if str(c).strip().lower() in ['office id', 'office_id']:
                    rename_map[c] = 'Office ID'
                    
            return df_to_clean[display_cols].rename(columns=rename_map)

        # Check if Admin has uploaded the monthly data into session state
        if st.session_state.monthly_df is not None:
            try:
                monthly_df = st.session_state.monthly_df.copy()

                # Find all available account types in the upload
                account_types = ['MIS', 'PPFGP', 'SSA', 'RD', 'SBBAS', 'SBSGP', 'SCSS', 'TD', 'PRFTS', 'KVN', 'NSC8', 'MSSC']
                available = [c for c in account_types if c in monthly_df.columns]
                
                monthly_df[available] = monthly_df[available].apply(pd.to_numeric, errors='coerce').fillna(0)
                monthly_df['Total_Monthly_Opened'] = monthly_df[available].sum(axis=1)

                final_df = pd.merge(display_df, monthly_df[['SOL_ID_BO_ID', 'Total_Monthly_Opened'] + available], on='SOL_ID_BO_ID', how='left')
                final_df[available + ['Total_Monthly_Opened']] = final_df[available + ['Total_Monthly_Opened']].fillna(0)
                
                # Top Metrics
                m1, m2, m3 = st.columns(3)
                tot_target = final_df['net target'].sum()
                tot_actual = final_df['Total_Monthly_Opened'].sum()
                m1.metric("Selected Circle Target", f"{tot_target:,.0f}")
                m2.metric("Monthly Achievement", f"{tot_actual:,.0f}")
                m3.metric("Achievement %", f"{(tot_actual/tot_target*100 if tot_target > 0 else 0):.2f}%")

                st.divider()

                # --- DYNAMIC DATA FILTER ---
                st.subheader("📊 Office Performance Filter")
                
                max_opened = int(final_df['Total_Monthly_Opened'].max()) if not final_df.empty and final_df['Total_Monthly_Opened'].max() > 0 else 100
                slider_max = max_opened + 5
                
                threshold = st.slider(
                    "Select Account Threshold (Show offices with LESS THAN this amount):", 
                    min_value=0, 
                    max_value=slider_max, 
                    value=slider_max, 
                    step=5
                )
                
                # Filter the master table
                filtered_df = final_df[final_df['Total_Monthly_Opened'] < threshold]
                
                if not filtered_df.empty:
                    if threshold == slider_max:
                        st.write(f"Showing **all {len(filtered_df)}** offices in the selected region.")
                    else:
                        st.warning(f"Found **{len(filtered_df)}** offices with fewer than {threshold} accounts opened.")
                    
                    # Include the total and all individual account types in the visible table
                    columns_to_add = ['Total_Monthly_Opened'] + available
                    clean_table = get_clean_table_columns(filtered_df, performance_cols=columns_to_add)
                    
                    st.dataframe(clean_table, use_container_width=True, hide_index=True)
                else:
                    st.success(f"🎉 No offices found with fewer than {threshold} accounts opened.")
                
            except Exception as e:
                st.error(f"Calculation Error: {e}")
        else:
            st.info("ℹ️ The monthly performance data has not been updated yet by an Administrator. Showing targets only.")
            st.subheader("Current Master Data Targets")
            
            m1, m2 = st.columns(2)
            tot_target = display_df['net target'].sum()
            m1.metric("Selected Region Target", f"{tot_target:,.0f}")
            m2.metric("Offices in Region", f"{len(display_df)}")
            
            # Show targets if monthly data isn't available
            clean_target_table = get_clean_table_columns(display_df, performance_cols=['net target'])
            st.dataframe(clean_target_table, use_container_width=True, hide_index=True)