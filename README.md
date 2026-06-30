# 🌾 ERP Data Analytics Pipeline – Tally ERP to PostgreSQL & Power BI

*An end-to-end ETL pipeline that ingests, cleans, and warehouses dealer sales and return data from Tally Prime ERP into PostgreSQL — enabling structured analytics and Power BI reporting for an agricultural inputs distribution business.*

---

## 📌 Table of Contents

- <a href="#overview">Overview</a>
- <a href="#Business Problem">Business Problem</a>
- <a href="#Dataset">Dataset</a>
- <a href="#Tools-&-Technologies">Tools & Technologies</a>
- <a href="#Project-Structure">Project Structure</a>
- <a href="#ETL-Pipeline–How-It-Works">ETL Pipeline – How It Works</a>
- <a href="#Data Cleaning & Transformation">Data Cleaning & Transformation</a>
- <a href="#Output Schema">Output Schema</a>
- <a href="#Dashboard">Dashboard</a>
- <a href="#Key Challenges Solved">Key Challenges Solved</a>
- <a href="#Key Insights Enabled">Key Insights Enabled</a>
- <a href="#Author & Contact">Author & Contact</a>

---

<h2><a class="anchor" id="overview"></a>Overview</h2>

This project automates the full data pipeline for **Ananymous Pvt. Ltd.**, an agricultural inputs distributor dealing in Chemicals and Fertilizer. Raw semi-structured Excel reports exported from Tally Prime ERP are cleaned, transformed, and loaded into a unified PostgreSQL table — which feeds a Power BI dashboard for business decision-making.

**Total rows processed: 42,197 transactions** across sales and returns.

---

<h2><a class="anchor" id="Business Problem"></a>Business Problem</h2>

Sales and return data at Ananymous Pvt Ltd lived entirely inside Tally ERP exports — semi-structured Excel files with merged rows, 9-row header offsets, nested voucher-item groupings, and split GST columns. There was no clean, queryable store.

This meant:
- No way to track dealer-wise performance across product categories
- Return rate analysis required hours of manual Excel work each month
- Discount trends (product discounts vs. cash discounts) were not comparable across dealers
- Pesticide and Fertilizer data were independently in separate unstructured files

**Goal:** Build a repeatable, automated ETL pipeline that unifies all four data streams into a single analytics-ready PostgreSQL table.

---

<h2><a class="anchor" id="Dataset"></a>Dataset</h2>

- **Source:** Tally Prime ERP → Excel export (`.xlsx`), 4 file types
- **Format:** Semi-structured with 9 header rows, hierarchical voucher→item row layout

---

<h2><a class="anchor" id="Tools-&-Technologies"></a>Tools & Technologies</h2>

- **Python** (Pandas, NumPy, SQLAlchemy, os, shutil)
- **PostgreSQL** (Data warehouse, unified `sales_transactions` table)
- **Tally Prime ERP** (Source system)
- **Power BI** (Dashboard and reporting)
- **Jupyter Notebook** (Development and execution)
- **SQL** (Exploratory Data Analysis)

---

## Project Structure

```
erp-data-analytics-pipeline/
│
├── README.md
├── .gitignore
│
├── Scripts/                           # ETL pipeline scripts
│   ├── clean_chemical.py              # Pesticide sales ETL
│   ├── clean_ferilizer.py             # Bio Stimulant sales ETL
│   ├── clean_chemreturn.py            # Pesticide returns ETL
│   └── clean_fertreturn.py            # Bio Stimulant returns ETL
│
├── dashboard/
│   └── data_project.pbix           # Power BI dashboard
│
└── images/
    └── dashboard.png               # Dashboard screenshot
```

---

<h2><a class="anchor" id="ETL-Pipeline–How-It-Works"></a>ETL Pipeline – How It Works</h2>


```
Tally Prime ERP
      │
      ▼
Raw Excel Export (.xlsx)  ──→  Raw/ folder
      │
      ▼
Python ETL (Pandas + SQLAlchemy)
  ├── Skip 9-row Tally header
  ├── Parse hierarchical voucher → item row structure
  ├── Extract dealer names, product names, discounts
  ├── Compute product discount & cash discount ratios
  ├── Anonymize dealer identities
  ├── Tag category and transaction type
  └── Load to PostgreSQL + save cleaned .xlsx
      │
      ▼
PostgreSQL  →  Power BI Dashboard
  └── Table: sales_transactions (unified, 42,197 rows)
```

Each script:
1. Reads from its `Raw/` folder
2. Cleans and transforms the data
3. Saves a cleaned `.xlsx` to `cleaned/` for audit trail
4. Loads all rows to the `sales_transactions` table in PostgreSQL
5. Deletes the raw file after successful load

---

<h2><a class="anchor" id="Data Cleaning & Transformation"></a>Data Cleaning & Transformation</h2>

### Parsing Tally's Hierarchical Export Format

Tally exports use a two-level row structure: **voucher rows** hold dealer names and totals, while **product rows** are nested below with quantity and rate. The pipeline resolves this:

```python
# Extract dealer name from voucher-level rows
df['dealer_name'] = df.loc[df['voucher_no'].notna() & df['Gross Total'].notna(), 'Particulars']
df['dealer_name'] = df['dealer_name'].ffill()

# Extract product name from item-level rows
df['products'] = df.loc[df['voucher_no'].isna() & df['rate'].notna(), 'Particulars']
```

### Two Types of Discount Computed

```python
# Product (trade) discount — computed per line item
df['product_discount'] = (df['Quantity'] * df['Rate'] - df['Value']) / (df['Quantity'] * df['Rate'])

# Cash discount — computed at voucher level, forward-filled to all items
df['cash_discount'] = df['Cash Discount'].fillna(0) / df['Sales']
df['cash_discount'] = df['cash_discount'].ffill()
```

### Return Quantity Sign Convention

Return quantities are negated so all transaction types flow consistently in analytics:

```python
df['quantity'] = df['quantity'] * -1
```

### Dealer Anonymization

Real dealer names are replaced with sequential IDs before any output is saved:

```python
dealer_map = {dealer: f"Dealer_{i+1:04d}" for i, dealer in enumerate(unique_dealers)}
df['dealer_name'] = df['dealer_name'].map(dealer_map)
```

---

<h2><a class="anchor" id="Output Schema"></a>Output Schema</h2>

### Table: `sales_transactions`

| Column | Type | Description |
|---|---|---|
| `date` | DATE | Transaction date |
| `voucher_no` | TEXT | Tally voucher number |
| `category` | TEXT | `chemical`, `Fertilizer`, `chemreturn`, `fertreturn` |
| `transaction_type` | TEXT | `sale` or `return` |
| `dealer_name` | TEXT | Anonymized dealer ID (`Dealer_0001`, ...) |
| `products` | TEXT | Product name |
| `quantity` | FLOAT | Units (negative for returns) |
| `rate` | FLOAT | Unit selling rate (₹) |
| `product_discount` | FLOAT | Trade discount ratio (0–1) |
| `cash_discount` | FLOAT | Cash discount ratio (0–1) |

---

<h2><a class="anchor" id="Dashboard"></a>Dashboard</h2>

The Power BI dashboard (`data_project.pbix`) connects directly to PostgreSQL and provides:

- Month-wise sales performance by product category
- Dealer-level volume and return rate analysis
- Product discount vs. cash discount trend tracking
- Net revenue estimation after returns

> 📸 *Dashboard screenshot — add `images/dashboard.png` to the repo*

---

<h2><a class="anchor" id="Key Challenges Solved"></a>Key Challenges Solved</h2>

- **Tally's non-tabular export format** — hierarchical voucher/item rows parsed using conditional row-level filtering and `.ffill()` logic; no standard tabular read worked out of the box
- **Two discount types in the same report** — product-level and voucher-level discounts isolated and computed independently
- **Inconsistent date formats across file types** — handled with `errors='coerce'` and format-specific `strptime` patterns
- **Four siloed data streams** — unified into a single `sales_transactions` table with `category` and `transaction_type` tags for cross-filter analysis
- **Dealer privacy** — real names anonymized before any file is saved or data is loaded

---


<h2><a class="anchor" id="Key Insights Enabled"></a>Key Insights Enabled</h2>

- Which dealers have the highest return rates by product category?
- Are cash discounts being given disproportionately to low-volume dealers?
- Which products carry the highest trade discount burden?
- How do monthly sales volumes compare across Pesticides vs. Bio Stimulants?
- What is the net revenue after factoring in both return volumes and discounts?

---

<h2><a class="anchor" id="Author & Contact"></a>Author & Contact</h2>

**Thirumala Reddy**  
Data Analyst — Nakasa Crop Science Pvt. Ltd.  
B.Tech, Computer Science & Engineering — NIT Andhra Pradesh  
📧 Email: thirumala.marreddy19@gmail.com  
🔗 [LinkedIn](www.linkedin.com/in/thirumala-reddy-1905deda)