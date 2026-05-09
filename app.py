import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="Postal Performance Tracker", layout="wide")

# --- 1. LOAD MASTER DATA ---
@st.cache_data
def load_master():
    try:
        df = pd.read_csv("master_data.csv")
        df.columns = [str(c).strip() for c in df.columns]
        
        if 'SOL_ID_BO_ID' in df.columns:
            df['SOL_ID_BO_ID'] = df['SOL_ID_BO_ID'].astype(str).str.strip()
        
        if 'office_type_code' in df.columns:
            df['office_type_code'] = df['office_type_code'].astype(str).str.strip().str.upper()
            
        return df
    except Exception as e:
        st.error(f"Error loading master_data.csv: {e}")
        return None

master_df = load_master()

# --- 2. APP UI & LOGIC ---
if master_df is not None:
    st.sidebar.title("📤 Data Management")
    uploaded_file = st.sidebar.file_uploader("Upload Weekly Account-wise File", type=["csv", "xlsx"])

    st.sidebar.divider()
    st.sidebar.header("📍 Geography Filter")
    
    if 'Division' in master_df.columns:
        div_list = sorted([str(x).strip() for x in master_df['Division'].dropna().unique().tolist()])
        sel_div = st.sidebar.selectbox("Select Division", ["All"] + div_list)

    # NEW: Low Performance Filter
    st.sidebar.divider()
    st.sidebar.header("⚠️ Performance Alerts")
    threshold = st.sidebar.slider("Show offices with less than X accounts:", 0, 100, 20)
    show_low_perf_only = st.sidebar.checkbox(f"Show only offices < {threshold}")

    st.title("📯 Postal Achievement Dashboard")

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                weekly_df = pd.read_csv(uploaded_file)
            else:
                weekly_df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            weekly_df.columns = [str(c).strip() for c in weekly_df.columns]
            
            if 'SOL ID / BOCODE' in weekly_df.columns:
                weekly_df = weekly_df.rename(columns={'SOL ID / BOCODE': 'SOL_ID_BO_ID'})
            
            weekly_df['SOL_ID_BO_ID'] = weekly_df['SOL_ID_BO_ID'].astype(str).str.strip()

            # Account types
            account_types = ['MIS', 'PPFGP', 'SSA', 'RD', 'SBBAS', 'SBSGP', 'SCSS', 'TD', 'PRFTS', 'KVN', 'NSC8', 'MSSC']
            available_accounts = [c for c in account_types if c in weekly_df.columns]
            
            weekly_df[available_accounts] = weekly_df[available_accounts].apply(pd.to_numeric, errors='coerce').fillna(0)
            weekly_df['Total_Weekly_Opened'] = weekly_df[available_accounts].sum(axis=1)

            # MERGE
            final_df = pd.merge(master_df, weekly_df[['SOL_ID_BO_ID', 'Total_Weekly_Opened'] + available_accounts], on='SOL_ID_BO_ID', how='left')
            
            # Fill missing matches with 0
            final_df[['Total_Weekly_Opened'] + available_accounts] = final_df[['Total_Weekly_Opened'] + available_accounts].fillna(0)
            final_df['Achievement_%'] = (final_df['Total_Weekly_Opened'] / final_df['net target'] * 100).round(2)

            if sel_div != "All":
                final_df = final_df[final_df['Division'] == sel_div]

            # Low/Zero Performance Dataframe
            low_perf_df = final_df[final_df['Total_Weekly_Opened'] < threshold].sort_values(by='Total_Weekly_Opened')

            # TOP METRICS
            m1, m2, m3 = st.columns(3)
            tot_target = final_df['net target'].sum()
            tot_actual = final_df['Total_Weekly_Opened'].sum()
            m1.metric("Monthly Net Target", f"{tot_target:,.0f}")
            m2.metric("Weekly Total Opened", f"{tot_actual:,.0f}")
            m3.metric("Achievement %", f"{(tot_actual/tot_target*100 if tot_target > 0 else 0):.2f}%")

            if show_low_perf_only:
                st.subheader(f"🚩 Offices with Low Performance (< {threshold} accounts)")
                st.write(f"Found **{len(low_perf_df)}** offices in this range.")
                st.dataframe(low_perf_df[['SOL_ID_BO_ID', 'Office_Name', 'office_type_code', 'Total_Weekly_Opened', 'Division']], use_container_width=True, hide_index=True)
            else:
                # NORMAL TABS
                st.divider()
                tab1, tab2, tab3, tab4 = st.tabs(["📌 Branch (BPO)", "🏢 Sub (SPO)", "🏛️ Head (HPO)", "🚨 Low/Zero Perf"])
                
                display_cols = ['SOL_ID_BO_ID', 'Office_Name', 'net target', 'Total_Weekly_Opened'] + available_accounts + ['Achievement_%']

                with tab1:
                    bpo = final_df[final_df['office_type_code'].str.contains('BPO|B.O', case=False, na=False)]
                    st.dataframe(bpo[display_cols], use_container_width=True, hide_index=True)
                with tab2:
                    spo = final_df[final_df['office_type_code'].str.contains('SPO|S.O', case=False, na=False)]
                    st.dataframe(spo[display_cols], use_container_width=True, hide_index=True)
                with tab3:
                    hpo = final_df[final_df['office_type_code'].str.contains('HPO|H.O', case=False, na=False)]
                    st.dataframe(hpo[display_cols], use_container_width=True, hide_index=True)
                with tab4:
                    st.subheader(f"Offices with < {threshold} Accounts")
                    st.write(f"This list includes all Zero performance offices.")
                    st.dataframe(low_perf_df[['SOL_ID_BO_ID', 'Office_Name', 'office_type_code', 'Total_Weekly_Opened', 'net target', 'Division']], use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error during calculation: {e}")
    else:
        st.info("👈 Please upload the weekly account-wise file.")