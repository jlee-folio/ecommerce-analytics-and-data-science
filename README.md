Online Retail Analytics: Developed a reproducible Python analytics pipeline that transforms transactional retail data into executive KPIs, sales and product performance analyses, customer-level metrics, RFM segments, pricing insights, and automated business reports. Includes data-quality assessment, documented metric definitions, and actionable recommendations for retail decision-making.

PROJECT OVERVIEW
•	This project delivers an end-to-end analysis of online retail transactions to uncover business insights into sales performance, customer purchasing behavior, product performance, and market trends. 
•	Using Python and data analytics techniques, the project transforms raw transactional data into structured business intelligence through data cleaning, exploratory data analysis (EDA), key performance indicator (KPI) development, customer segmentation, and data visualization. 
•	The objective is to demonstrate how a data-driven approach can support strategic decision-making in customer retention, product management, sales optimization, and market development.
•	This project is designed as part of a Senior Data Scientist portfolio, demonstrating practical skills in data preparation, analytical problem-solving, business interpretation, and automated reporting.

BUSINESS OBJECTIVE
The analysis addresses the following business questions:
•	Sales Performance: How does revenue change over time, and which periods generate the highest and lowest sales?
•	Customer Behavior: Who are the highest-value customers, and how do purchasing frequency and spending patterns differ?
•	Customer Segmentation: Which customers can be classified as Champions, Loyal Customers, At Risk, Hibernating, or Potential Loyalists?
•	Product Performance: Which products generate the most revenue, attract the most customers, and sell the highest quantities?
•	Geographic Performance: Which countries contribute the most to revenue and order volume?
•	Pricing Analysis: How do observed product prices relate to sales volume and revenue?
•	Hourly Sales Patterns: At what times of day is revenue highest?
•	Business Recommendations: How can the findings inform customer retention, product prioritization, marketing activities, and operational planning?

DATASET DESCRIPTION
Dataset: Online Retail Transactions Dataset
Source: Kaggle — Online Retail Transactions Dataset
The dataset contains transactional records from an online retail business. It includes information about products, quantities purchased, invoice dates, unit prices, customer identifiers, and customer countries.
These data support the investigation of sales trends, customer purchasing patterns, product performance, and geographic differences in retail activity.
Data Dictionary
•	StockCode:	Identifier used to distinguish products.
•	Description:	Product description.
•	Quantity:	Number of units recorded for a transaction line.
•	InvoiceDate:	Date and time associated with the invoice.
•	UnitPrice:	Price per unit recorded in the transaction.
•	CustomerID:	Identifier associated with a customer, where available.
•	Country:	Country associated with the customer.
Depending on the source file, additional fields such as InvoiceNo may be available and are used to identify invoices and calculate order-level metrics. Each row represents a transaction line rather than necessarily a complete customer order. Multiple rows may belong to the same invoice.

ANALYTICAL METHODOLOGY
1. Data Ingestion and Quality Assessment
•	Load transaction data using Pandas.
•	Inspect data types, missing values, unique values, and duplicate records.
•	Generate a data-quality report to assess completeness and identify potential data issues.
•	Standardize column names and convert dates and numerical fields to appropriate data types.
2. Data Cleaning and Feature Engineering
•	Remove duplicate records.
•	Handle missing or invalid values in essential transaction fields.
•	Exclude records with non-positive quantities or unit prices according to the project's cleaning rules.
•	Calculate transaction-line revenue as quantity multiplied by unit price.
•	Extract temporal features, including year, month, day, weekday, and hour.
•	Create a year-month variable for time-series aggregation.
These rules establish a consistent analytical dataset. However, excluding non-positive quantities means that returns and cancellations may not be fully represented in the resulting sales metrics.
3. Executive KPI Analysis
Calculate core business metrics, including:
•	Total recorded revenue.
•	Number of distinct invoices.
•	Number of identifiable customers.
•	Number of distinct products.
•	Total units sold.
•	Average order value (AOV).
•	Average unit price.
These KPIs provide a high-level overview of sales activity and business scale.
4. Sales Trend Analysis
•	Aggregate revenue, orders, customers, and units sold by month.
•	Calculate monthly average order value.
•	Visualize monthly revenue trends.
•	Identify the highest- and lowest-revenue months for further investigation.
5. Product Performance Analysis
•	Rank products by total revenue.
•	Analyze units sold, distinct invoices, and customer reach.
•	Calculate product revenue contribution.
•	Visualize the highest-revenue products.
6. Customer Analytics
•	Aggregate transaction activity at the customer level.
•	Calculate customer revenue, order count, units purchased, and product variety.
•	Calculate average order value and customer activity duration.
•	Examine the distribution of customer revenue to understand differences in spending behavior.
7. RFM Customer Segmentation
Apply Recency, Frequency, and Monetary (RFM) analysis to group customers according to their historical purchasing behavior.
•	Recency: Time elapsed since the customer's most recent purchase.
•	Frequency: Number of distinct invoices associated with the customer.
•	Monetary: Total recorded revenue
Customers receive relative quintile-based scores and are assigned interpretable segments:
•	Champions
•	Loyal Customers
•	At Risk
•	Hibernating
•	Potential Loyalists
These segments can help prioritize customer retention and re-engagement initiatives. They are rule-based analytical categories, not direct predictions of future customer behavior.
8. Geographic Performance Analysis
•	Aggregate revenue, invoices, customers, and units by country.
•	Rank countries by recorded revenue.
•	Compare average order value and customer counts across markets.
9. Product Pricing Analysis
•	Calculate average and median observed prices by product.
•	Compare pricing patterns with units sold, invoice counts, and revenue.
•	Identify product-level patterns for further investigation.
The analysis is descriptive and does not establish a causal relationship between price and demand.
10. Hourly Sales Analysis
•	Aggregate revenue, orders, and units by transaction hour.
•	Visualize hourly revenue patterns.
•	Identify periods of high recorded sales activity that may warrant further operational analysis.
11. Automated Reporting
Generate a Microsoft Word report containing:
•	Executive KPI summaries.
•	Data-quality findings.
•	Sales and product performance tables.
•	Customer analytics and RFM segmentation results.
•	Geographic and pricing analysis.
•	Embedded visualizations.
•	Business interpretations, recommendations, and analytical limitations.
Export detailed analytical outputs to CSV files to support further investigation and reporting.
