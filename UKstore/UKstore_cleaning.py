import pandas as pd

# LOAD THE DATA
print("Loading data...")
df1 = pd.read_excel("online_retail_II.xlsx", sheet_name="Year 2010-2011")
df2 = pd.read_excel("online_retail_II.xlsx", sheet_name="Year 2010-2011")

# APPEND THE TWO FILES
df = pd.concat([df1,df2], axis = 0)

# === Step 2: Drop fully missing columns ===
df.dropna(axis=1, how='all', inplace=True)

# === Step 3: Remove rows with missing critical data ===
df = df[df['Invoice'].notna()]
df = df[df['StockCode'].notna()]
df = df[df['Quantity'].notna()]
df = df[df['UnitPrice'].notna()]

# === Step 4: Convert data types ===
df['Invoice'] = df['Invoice'].astype(str)
df['StockCode'] = df['StockCode'].astype(str)
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['Customer ID'] = df['Customer ID'].astype('Int64')  # Nullable int

# === Step 5: Remove invalid transactions ===
df = df[df['Quantity'] != 0]
df = df[df['UnitPrice'] > 0]

# Optional: remove non-product codes (adjust as needed)
non_product_keywords = ['POST', 'BANK CHARGES', 'CARRIAGE', 'ADJUST', 'SAMPLES']
df = df[~df['Description'].str.upper().isin(non_product_keywords)]

# === Step 6: Add calculated fields ===
df['Sales'] = df['Quantity'] * df['UnitPrice']
df['IsReturn'] = df['Invoice'].str.startswith('C') | (df['Quantity'] < 0)

# === Step 7: Standardize text fields ===
df['Description'] = df['Description'].str.strip().str.lower()
df['Country'] = df['Country'].str.strip()

# === Step 8: Enrich with date parts ===
df['Year'] = df['InvoiceDate'].dt.year
df['Month'] = df['InvoiceDate'].dt.month
df['MonthName'] = df['InvoiceDate'].dt.strftime('%B')
df['Weekday'] = df['InvoiceDate'].dt.day_name()

# === Step 9: Flag first-time customers (optional) ===
customer_first_dates = df.groupby('Customer ID')['InvoiceDate'].min()
df['FirstPurchaseDate'] = df['Customer ID'].map(customer_first_dates)
df['IsFirstPurchase'] = df['InvoiceDate'] == df['FirstPurchaseDate']

# === Step 10: Drop duplicates (if any) ===
df = df.drop_duplicates()

# === Step 11: Export cleaned data ===
output_file = "cleaned_online_retail_data.xlsx"
df.to_excel(output_file, index=False)
print(f"Cleaned data exported to: {output_file}")
