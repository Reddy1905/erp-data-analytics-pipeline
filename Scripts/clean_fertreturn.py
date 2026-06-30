import os
import shutil
import pandas as pd
import numpy as np

from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://postgres:123456@localhost:5432/nakasa_crop_science"
)

raw_folder = r'F:\BioReturns\Raw'
cleaned_folder = r'F:\BioReturns\cleaned'

def clean_fertreturn(file_path,output_path):
    print(f"cleaning: {os.path.basename(file_path)}")

    df = pd.read_excel(file_path , skiprows = 9)
    df.columns = df.columns.str.strip()

    df = df.drop(['Voucher Ref. No.','Voucher Ref. Date','Round Off','Stock Return','CGST','IGST','SGST'],axis = 1)
    df = df.rename(columns={'Date': 'date',
                         'Voucher No.' : 'voucher_no',
                          'Quantity' : 'quantity',
                          'Rate' : 'rate'
                         })
    df['date']=pd.to_datetime(df['date'],format = '%d-%M-%Y',errors = 'coerce')
    df['date'] = df['date'].ffill()
    df['dealer_name'] = df.loc[df['voucher_no'].notna() & df['Gross Total'].notna(),'Particulars']
    df['dealer_name'] = df['dealer_name'].ffill()
    df['products'] = df.loc[df['voucher_no'].isna() & df['rate'].notna(),'Particulars']
    df['product_discount']= (df['quantity']*df['rate']-df['Value'])/(df['quantity']*df['rate'])
    df['cash_discount']= df['Cash Discount'].fillna(0)/df['Sales']
    df['cash_discount']=df['cash_discount'].ffill()
    df=df.drop(['Value','Gross Total','Sales','Cash Discount'],axis = 1)
    df['voucher_no']=df['voucher_no'].ffill()
    df = df.dropna(subset = 'products')
    df.reset_index(drop = True , inplace = True)
    df['quantity']= df['quantity']*-1
    df=df.drop(['Particulars'], axis = 1)
    df['category']= 'fertreturn'
    df['transaction_type'] = 'return'
    col=['date','voucher_no','category','transaction_type','dealer_name','products','quantity','rate','product_discount','cash_discount']
    df=df[col]
    unique_dealers = df['dealer_name'].drop_duplicates()

    dealer_map = {
        dealer: f"Dealer_{i+1:04d}"
        for i, dealer in enumerate(unique_dealers)
    }

    df['dealer_name'] = df['dealer_name'].map(dealer_map)
    df.to_excel(output_path,index = False)
    print(f"Cleaned file saved: {output_path}")

    df.to_sql(
        'sales_transactions',
        con=engine,
        if_exists='append',
        index=False,
        method='multi'
    )

    print(f"{len(df)} rows loaded to PostgreSQL")

print(f'Watching folder: {raw_folder}')

for file in os.listdir(raw_folder):
    if file.endswith('.xlsx'):
        source_path = os.path.join(raw_folder, file)
        cleaned_path = os.path.join(cleaned_folder, f"cleaned_{file}")

        clean_fertreturn(source_path, cleaned_path)

        os.remove(source_path)
        print(f"Deleted raw file: {file}")

print("All files processed successfully")