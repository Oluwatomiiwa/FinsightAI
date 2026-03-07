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
    # 4. Dashboard Metrics
    total_debit = sum(item['amount'] for item in data if item['transaction_type'] == 'debit')
    total_credit = sum(item['amount'] for item in data if item['transaction_type'] == 'credit')
    
    m1, m2 = st.columns(2)
    m1.metric("Total Outflow", f"₦{total_debit:,.2f}")
    m2.metric("Total Inflow", f"₦{total_credit:,.2f}")
    
    # 5. --- AI SPENDING INSIGHTS (Week-to-Date) ---
    st.markdown("---")
    st.subheader("🧠 Pacing Insights")
    
    # Convert data to a Pandas DataFrame to do date math easily
    df = pd.DataFrame(data)
    
    # We only care about money leaving your account (debits) for spending alerts
    df_spend = df[df['transaction_type'] == 'debit'].copy()
    
    if not df_spend.empty:
        # Ensure dates are recognized properly (FIXED: changed 'date' to 'transaction_date')
        df_spend['transaction_date'] = pd.to_datetime(df_spend['transaction_date'])
        
        # Get today's time and day of the week
        today = dt.datetime.now()
        current_year = today.year
        current_week = today.isocalendar()[1]
        day_of_week = today.weekday() # Monday = 0, Sunday = 6
        
        # Calculate CURRENT Week-to-Date (WTD) spend
        current_wtd_df = df_spend[(df_spend['transaction_date'].dt.year == current_year) & 
                                  (df_spend['transaction_date'].dt.isocalendar().week == current_week) & 
                                  (df_spend['transaction_date'].dt.weekday <= day_of_week)]
        current_wtd_spend = current_wtd_df['amount'].sum()
        
        # Calculate PAST Week-to-Date spend (up to this exact day in previous weeks)
        past_wtd_df = df_spend[(df_spend['transaction_date'].dt.isocalendar().week != current_week) & 
                               (df_spend['transaction_date'].dt.weekday <= day_of_week)]
        
        # The Alert Engine
        if past_wtd_df.empty:
            st.info(f"📊 **Gathering data:** You've spent **₦{current_wtd_spend:,.2f}** so far this week. I'm learning your habits to give you pacing alerts next week!")
        else:
            # Group past data by week to find the average
            past_weeks_grouped = past_wtd_df.groupby([past_wtd_df['transaction_date'].dt.year, past_wtd_df['transaction_date'].dt.isocalendar().week])['amount'].sum()
            avg_past_wtd_spend = past_weeks_grouped.mean()
            
            if current_wtd_spend > avg_past_wtd_spend:
                st.error(f"⚠️ **Careful!** You've spent **₦{current_wtd_spend:,.2f}** this week. You are spending more than your usual ₦{avg_past_wtd_spend:,.2f} by this time of the week.")
            elif current_wtd_spend < avg_past_wtd_spend:
                st.success(f"✅ **Well done!** You've spent **₦{current_wtd_spend:,.2f}** this week. You have spent lesser than your usual ₦{avg_past_wtd_spend:,.2f} around this time.")
            else:
                st.info(f"⚖️ **Right on track.** You are matching your usual spending pace.")
                
    # --- MONTHLY SPENDING TREND ---
    st.write("### 📊 Monthly Spending Trend")
    
    # 1. Tell Pandas to extract just the Month and Year from the exact dates
    df_spend['month'] = df_spend['transaction_date'].dt.to_period('M').astype(str)
    
    # 2. Tell Pandas to group everything by that new 'month' column and add up the amounts
    monthly_spend = df_spend.groupby('month')['amount'].sum().reset_index()
    
    # 3. Tell Streamlit to draw a bar chart using the Pandas math!
    st.bar_chart(data=monthly_spend, x='month', y='amount')
    
    # 6. --- TRANSACTION LEDGER ---
    st.markdown("---")
    st.write("### 📜 Transaction Ledger")
    # Sort by date so newest is on top, and hide the index for a cleaner look
    st.dataframe(df.sort_values(by='transaction_date', ascending=False), use_container_width=True, hide_index=True)

else:
    st.info("FinsightAI is ready. Awaiting data from the n8n pipeline...")