import pandas as pd
import numpy as np

# LOAD THE DATA
print("Loading data...")
df1 = pd.read_excel("online_retail_II.xlsx", sheet_name="Year 2010-2011")
df2 = pd.read_excel("online_retail_II.xlsx", sheet_name="Year 2009-2010")
print("Data loaded")

# APPEND THE TWO FILES
df1['datayear'] = "2010-2011"
df2['datayear'] = "2009-2010"
df = pd.concat([df1,df2], axis = 0)

# EXPLORE THE DATA
print(df.info())
print(df.head())
print(df.describe())
print(df.isnull().mean() * 100)

#   check for 0s:: 0 wouldn't make sense
if 0 in df['Price'].value_counts():
    print('Price has 0s')
if 0 in df['Quantity'].value_counts():
    print('Quantity has 0s')

#  0's related to missing data in the customer id and description?
#   Most are missing, feel comfortable dropping these
zCheck = df.loc[df['Price'] == 0]['Customer ID'].isna().value_counts()
print(f"{zCheck.get(True,0)} Customer IDs are missing when price == 0. {zCheck.get(False,0)} are not missing")
# === Step 5: Remove invalid transactions ===
print(f'{len(df.loc[df['Price'] == 0])} transactions with 0 cost will be removed')
df = df.loc[df['Price'] != 0]


# Check for duplicates
x = len(df)
y = len(df.drop_duplicates())
if x != y:
    print(f'There are {x - y} Duplicates')
    print('Dropping duplicates')
    df = df.drop_duplicates()

# Weird stock codes, those that are all characters, 
print(df.loc[df['StockCode'].astype(str).str.isalpha()==True]['Description'].value_counts())
x = len(df)
non_product_keywords = ['postage', 'dot compostage', 'amazon fee']
print(f'dropping those with a description in this list {non_product_keywords} or has "asjustment"')
df = df[~df['Description'].str.lower().isin(non_product_keywords)]
df = df[~df['Description'].str.lower().str.contains('adjust', na=False)]
y = len(df)
print(f'{x-y} transactions were dropped.')




# === Step 6: Add calculated fields ===
df['Sales'] = df['Quantity'] * df['Price']
df['IsReturn'] = np.where(df['Invoice'].str.startswith('C') | (df['Quantity'] < 0), 1, 0)
print("Created IsReturn when Invoice starts with C or Quantity < 0")
print(df['IsReturn'].value_counts())
print(df.loc[df['IsReturn']==1]['Sales'].describe())
#No sales should be positive on a return, fix it
df.loc[df['IsReturn']==1,['Sales']] = df.loc[df['IsReturn']==1,['Sales']].abs()*-1
if df.loc[df['IsReturn']==1]['Sales'].describe()['max'] > -0:
    "Returned value 0  or greater"

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
df['IsFirstPurchase'] = np.where(df['InvoiceDate'] == df['FirstPurchaseDate'], 1, 0)
print(df['IsFirstPurchase'].value_counts())


## Let's explore the data with crosstabs and the important data
pd.crosstab(index=df['Country'], columns=df['IsReturn'], normalize='index').sort_values(1, ascending= False)
pd.crosstab(index=df['datayear'], columns=df['IsReturn'], normalize='index').sort_values(1, ascending= False)
pd.crosstab(index=df['Country'], columns=df['IsFirstPurchase'], normalize='index').sort_values(1, ascending= False)
pd.crosstab(index=df['datayear'], columns=df['IsFirstPurchase'], normalize='index').sort_values(1, ascending= False)
pd.crosstab(index=df['Country'], columns=df['datayear'], values=df['Sales'], aggfunc='sum')
    #Nigeria only has negative values. 



# === Step 11: Export cleaned data ===
output_file = "cleaned_online_retail_data.csv"
df.to_csv(output_file, index=False)
print(f"Cleaned data exported to: {output_file}")
