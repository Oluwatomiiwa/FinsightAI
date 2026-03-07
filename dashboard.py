import pandas as pd
from supabase import create_client, Client

# 1. Paste your Supabase credentials here
SUPABASE_URL = "https://rlqqowkcbunotukflvau.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJscXFvd2tjYnVub3R1a2ZsdmF1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI2NTAxNzQsImV4cCI6MjA4ODIyNjE3NH0.0vL87E8yQBDv-UEKeU9ViDhNqB7WaPM1TSM8tgBO5ZE"

# 2. Connect to the vault
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Pull the data (Change 'transactions' to your actual Supabase table name!)
response = supabase.table("transactions").select("*").execute()

# 4. Convert the data into a Pandas DataFrame
df = pd.DataFrame(response.data)

# 5. Print the first 5 rows to make sure it worked
print("Data loaded successfully! Here is a sneak peek:")
print(df.head())