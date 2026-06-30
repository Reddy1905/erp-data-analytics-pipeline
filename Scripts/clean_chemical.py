import os
import shutil
import pandas as pd
import numpy as np

from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://postgres:123456@localhost:5432/nakasa_crop_science"
)

raw_folder = r'F:\Pesticides\Raw'
cleaned_folder = r'F:\Pesticides\cleaned'

def clean_chemical(file_path,output_path):
    print(f"cleaning: {os.path.basename(file_path)}")

    df = pd.read_excel(file_path , skiprows = 9)
    df.columns = df.columns.str.strip()
    df = df.drop(['Round Off','Voucher Ref. No.'],axis = 1)
    df['Date']=pd.to_datetime(df['Date'],format = '%d-%m-%y')
    df['Date'] = df['Date'].dt.date
    df['Date'] = df['Date'].ffill()
    df['Voucher No.'] = df['Voucher No.'].ffill()
    df = df.drop(['CGST','SGST','IGST'],axis = 1)
    df['dealer_name']=df.loc[df['Rate'].isna() & df['Gross Total'].notna(),'Particulars']
    df['products']=df.loc[df['Quantity'].notna() & df['Rate'].notna(),'Particulars']
    df['dealer_name']= df['dealer_name'].ffill()
    df['product_discount']= (df['Quantity']*df['Rate']-df['Value'])/(df['Quantity']*df['Rate'])
    df['cash_discount']= df['CD on Pesticides Sales'].fillna(0)/df['Pesticides Sales']
    df['cash_discount']= df['cash_discount'].ffill()
    df=df.dropna(subset = 'products')
    df = df.rename(columns={'Date' : 'date','Voucher No.':'voucher_no','Quantity':'quantity','Rate':'rate'})
    df['category']= 'chemical'
    df['transaction_type'] = 'sale'
    col=['date','voucher_no','category','transaction_type','dealer_name','products','quantity','rate','product_discount','cash_discount']
    df = df[col]
    df = df.reset_index(drop = True)


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

        clean_chemical(source_path, cleaned_path)

        os.remove(source_path)
        print(f"Deleted raw file: {file}")

print("All files processed successfully")