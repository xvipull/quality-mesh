-- Logical star schema for the Sales Orders pilot. SQLite DDL is executed by pipeline.py.
-- Fact grain: one row per sales order; reconciliation fact grain: one source control per date/system/currency.
CREATE TABLE dim_date (
  date_key INTEGER PRIMARY KEY,
  calendar_date DATE NOT NULL UNIQUE,
  year INTEGER NOT NULL,
  month INTEGER NOT NULL,
  day INTEGER NOT NULL
);

CREATE TABLE dim_customer (
  customer_key INTEGER PRIMARY KEY,
  customer_id TEXT NOT NULL UNIQUE,
  customer_name TEXT NOT NULL,
  segment TEXT NOT NULL,
  status TEXT NOT NULL,
  created_date DATE NOT NULL
);

CREATE TABLE dim_category (
  category_key INTEGER PRIMARY KEY,
  category_code TEXT NOT NULL UNIQUE
);

CREATE TABLE fact_sales_order (
  order_key INTEGER PRIMARY KEY,
  order_id TEXT NOT NULL UNIQUE,
  customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
  order_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
  category_key INTEGER NOT NULL REFERENCES dim_category(category_key),
  order_amount DECIMAL(18,2) NOT NULL,
  currency_code CHAR(3) NOT NULL
);
