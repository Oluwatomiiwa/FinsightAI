import streamlit as st
import pandas as pd
import datetime as dt
from supabase import create_client, Client

# Browser Tab Branding (MUST be the first Streamlit command)
st.set_page_config(page_title="FinsightAI", page_icon="📊")

# 1. Pull credentials from the secrets file instead of hardcoding them
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# 2. Main Interface
st.title("🚀 FinsightAI")
st.subheader("Intelligent Financial Insights Engine")
st.markdown("---")

# 3. Fetch Data
def get_data():
    try:
        # Pulling from your transactions table
        response = supabase.table("transactions").select("*").execute()
        return response.data
    except Exception as e:
        st.error(f"Vault Connection Error: {e}")
        return []

data = get_data()

if data:
    # 4. --- ADVANCED MONTHLY METRICS ---
    df_metrics = pd.DataFrame(data)
    df_metrics['transaction_date'] = pd.to_datetime(df_metrics['transaction_date'])
    
    # Get current and last month periods
    current_month_period = pd.Timestamp.now().to_period('M')
    last_month_period = (pd.Timestamp.now() - pd.DateOffset(months=1)).to_period('M')

    # Calculate Totals for Current Month
    cur_month_debit = df_metrics[(df_metrics['transaction_date'].dt.to_period('M') == current_month_period) & (df_metrics['transaction_type'] == 'debit')]['amount'].sum()
    cur_month_credit = df_metrics[(df_metrics['transaction_date'].dt.to_period('M') == current_month_period) & (df_metrics['transaction_type'] == 'credit')]['amount'].sum()

    # Calculate Totals for Last Month
    last_month_debit = df_metrics[(df_metrics['transaction_date'].dt.to_period('M') == last_month_period) & (df_metrics['transaction_type'] == 'debit')]['amount'].sum()
    
    # Calculate Percentage Change for Outflow
    if last_month_debit > 0:
        delta_val = ((cur_month_debit - last_month_debit) / last_month_debit) * 100
        delta_text = f"{delta_val:+.1f}% vs last month"
    else:
        delta_text = "New data track" # Shows this if Feb has 0 transactions

    # Display the Metrics with Deltas
    m1, m2 = st.columns(2)
    # The 'delta_color' is 'inverse' because for spending, an increase (positive) is usually "bad" (red)
    m1.metric("Total Outflow", f"₦{cur_month_debit:,.2f}", delta=delta_text, delta_color="inverse")
    m2.metric("Total Inflow", f"₦{cur_month_credit:,.2f}")
    
    # 5. --- AI SPENDING INSIGHTS (Week-to-Date) ---
    st.markdown("---")
    st.subheader("🧠 Pacing Insights")
    
    # Convert data to a Pandas DataFrame for calculations
    df = pd.DataFrame(data)
    df_spend = df[df['transaction_type'] == 'debit'].copy()
    
    if not df_spend.empty:
        df_spend['transaction_date'] = pd.to_datetime(df_spend['transaction_date'])
        
        today = dt.datetime.now()
        current_year = today.year
        current_week = today.isocalendar()[1]
        day_of_week = today.weekday() 
        
        # Calculate CURRENT Week-to-Date (WTD) spend
        current_wtd_df = df_spend[(df_spend['transaction_date'].dt.year == current_year) & 
                                  (df_spend['transaction_date'].dt.isocalendar().week == current_week) & 
                                  (df_spend['transaction_date'].dt.weekday <= day_of_week)]
        current_wtd_spend = current_wtd_df['amount'].sum()
        
        # Calculate PAST Week-to-Date spend
        past_wtd_df = df_spend[(df_spend['transaction_date'].dt.isocalendar().week != current_week) & 
                               (df_spend['transaction_date'].dt.weekday <= day_of_week)]
        
        if past_wtd_df.empty:
            st.info(f"📊 **Gathering data:** You've spent **₦{current_wtd_spend:,.2f}** so far this week. I'm learning your habits to give you pacing alerts next week!")
        else:
            past_weeks_grouped = past_wtd_df.groupby([past_wtd_df['transaction_date'].dt.year, past_wtd_df['transaction_date'].dt.isocalendar().week])['amount'].sum()
            avg_past_wtd_spend = past_weeks_grouped.mean()
            
            if current_wtd_spend > avg_past_wtd_spend:
                st.error(f"⚠️ **Careful!** You've spent **₦{current_wtd_spend:,.2f}** this week. You are spending more than your usual ₦{avg_past_wtd_spend:,.2f} by this time.")
            elif current_wtd_spend < avg_past_wtd_spend:
                st.success(f"✅ **Well done!** You've spent **₦{current_wtd_spend:,.2f}** this week. You have spent lesser than your usual ₦{avg_past_wtd_spend:,.2f}.")
            else:
                st.info(f"⚖️ **Right on track.** You are matching your usual spending pace.")
                
    # --- MONTHLY SPENDING TREND ---
    st.write("### 📊 Monthly Spending Trend")
    df_spend['month'] = df_spend['transaction_date'].dt.to_period('M').astype(str)
    monthly_spend = df_spend.groupby('month')['amount'].sum().reset_index()
    st.bar_chart(data=monthly_spend, x='month', y='amount')
    
    # 6. --- TRANSACTION LEDGER ---
    st.markdown("---")
    st.write("### 📜 Transaction Ledger")
    st.dataframe(df.sort_values(by='transaction_date', ascending=False), use_container_width=True, hide_index=True)

else:
    st.info("FinsightAI is ready. Awaiting data from the n8n pipeline...")