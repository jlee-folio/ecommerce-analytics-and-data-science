# ============================================================
# ONLINE RETAIL CUSTOMER ANALYTICS
# Sales, Products, Customers, RFM and Word Reporting
# ============================================================

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

warnings.filterwarnings("default")

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

RANDOM_STATE = 42

# All paths are relative to this Python file.
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_PATH = DATA_DIR / "online_retail.csv"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", context="notebook")

pd.set_option("display.max_columns", 100)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")


# ------------------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------------------

def load_data(path=DATA_PATH):
    """Load the source CSV file and validate required columns."""

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {path}\n"
            "Place online_retail.csv in the project's data folder."
        )

    df = pd.read_csv(path, low_memory=False)

    # Standardize column names.
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(" ", "_", regex=False)
        .str.lower()
    )

    required = {
        "invoiceno", "stockcode", "description",
        "quantity", "invoicedate", "unitprice",
        "customerid", "country"
    }

    missing = required.difference(df.columns)

    if missing:
        raise ValueError(
            f"Required columns are missing: {sorted(missing)}\n"
            f"Available columns: {df.columns.tolist()}"
        )

    print("\nDATASET LOADED")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")

    return df


# ------------------------------------------------------------
# 3. DATA QUALITY PROFILE
# ------------------------------------------------------------

def profile_data(df):
    """Summarize missing values, data types and unique values."""

    profile = pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.astype(str).values,
        "missing_count": df.isna().sum().values,
        "missing_pct": (df.isna().mean() * 100).values,
        "unique_values": df.nunique().values
    })

    return profile.sort_values(
        "missing_pct", ascending=False
    ).reset_index(drop=True)


# ------------------------------------------------------------
# 4. CLEAN DATA
# ------------------------------------------------------------

def clean_data(df):
    """
    Clean transaction records.

    Excludes duplicates, invalid dates, missing essential
    transaction fields, and non-positive quantities/prices.
    Missing customer IDs are retained for sales analysis.
    """

    data = df.copy()

    before = len(data)
    data = data.drop_duplicates().copy()

    print(f"Duplicate rows removed: {before - len(data):,}")

    data["invoicedate"] = pd.to_datetime(
        data["invoicedate"], errors="coerce"
    )

    for column in ["quantity", "unitprice"]:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    data["customerid"] = pd.to_numeric(
        data["customerid"], errors="coerce"
    )

    # Remove records that cannot support transaction analysis.
    data = data.dropna(subset=[
        "invoiceno", "stockcode", "description",
        "invoicedate", "quantity", "unitprice"
    ])

    data["description"] = data["description"].astype(str).str.strip()

    data = data[
        (data["description"] != "") &
        (data["quantity"] > 0) &
        (data["unitprice"] > 0)
    ].copy()

    # Revenue is calculated from the retained positive sales lines.
    data["revenue"] = data["quantity"] * data["unitprice"]

    # Date and time features.
    data["year"] = data["invoicedate"].dt.year
    data["month"] = data["invoicedate"].dt.month
    data["month_name"] = data["invoicedate"].dt.month_name()
    data["week"] = data["invoicedate"].dt.isocalendar().week.astype(int)
    data["day"] = data["invoicedate"].dt.day
    data["day_name"] = data["invoicedate"].dt.day_name()
    data["hour"] = data["invoicedate"].dt.hour
    data["year_month"] = data["invoicedate"].dt.to_period("M").astype(str)

    # Nullable integer representation for customer IDs.
    data["customerid"] = data["customerid"].round().astype("Int64")

    print(f"Rows retained after cleaning: {len(data):,}")
    print(f"Rows removed overall: {before - len(data):,}")
    print(f"Missing customer IDs retained: {data['customerid'].isna().sum():,}")

    return data


# ------------------------------------------------------------
# 5. EXECUTIVE KEY PERFORMANCE INDICATORS
# ------------------------------------------------------------

def calculate_kpis(df):
    """Calculate headline business metrics."""

    order_revenue = df.groupby("invoiceno")["revenue"].sum()

    kpis = {
        "Total Revenue": df["revenue"].sum(),
        "Total Orders": df["invoiceno"].nunique(),
        "Unique Customers": df["customerid"].nunique(),
        "Unique Products": df["stockcode"].nunique(),
        "Units Sold": df["quantity"].sum(),
        "Average Order Value": order_revenue.mean(),
        "Average Unit Price": df["unitprice"].mean(),
        "Average Revenue per Identified Customer": (
            df.groupby("customerid")["revenue"].sum().mean()
        )
    }

    return pd.Series(kpis, name="value")

    # ------------------------------------------------------------
# 6. MONTHLY SALES ANALYSIS
# ------------------------------------------------------------

def monthly_sales(df):
    monthly = (
        df.groupby("year_month")
        .agg(
            revenue=("revenue", "sum"),
            orders=("invoiceno", "nunique"),
            customers=("customerid", "nunique"),
            units=("quantity", "sum")
        )
        .reset_index()
        .sort_values("year_month")
    )

    monthly["aov"] = monthly["revenue"] / monthly["orders"]
    return monthly


def plot_monthly_revenue(monthly):
    if monthly.empty:
        return

    plt.figure(figsize=(14, 6))
    sns.lineplot(data=monthly, x="year_month", y="revenue", marker="o")
    plt.title("Monthly Revenue Trend")
    plt.xlabel("Month")
    plt.ylabel("Revenue")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "monthly_revenue.png", dpi=200)
    plt.close()


# ------------------------------------------------------------
# 7. PRODUCT ANALYSIS
# ------------------------------------------------------------

def top_products(df, n=20):
    products = (
        df.groupby(["stockcode", "description"], dropna=False)
        .agg(
            revenue=("revenue", "sum"),
            units_sold=("quantity", "sum"),
            orders=("invoiceno", "nunique"),
            customers=("customerid", "nunique")
        )
        .reset_index()
    )

    total = products["revenue"].sum()
    products["revenue_share"] = (
        products["revenue"] / total if total else 0
    )

    return products.sort_values(
        "revenue", ascending=False
    ).head(n).reset_index(drop=True)


def plot_top_products(products):
    if products.empty:
        return

    plot_data = products.sort_values("revenue", ascending=True)

    plt.figure(figsize=(12, 8))
    sns.barplot(data=plot_data, x="revenue", y="description")
    plt.title("Top Products by Revenue")
    plt.xlabel("Revenue")
    plt.ylabel("Product")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "top_products_revenue.png", dpi=200)
    plt.close()


# ------------------------------------------------------------
# 8. CUSTOMER METRICS
# ------------------------------------------------------------

def customer_metrics(df):
    identified = df.dropna(subset=["customerid"])

    customer = (
        identified.groupby("customerid")
        .agg(
            revenue=("revenue", "sum"),
            orders=("invoiceno", "nunique"),
            units=("quantity", "sum"),
            products=("stockcode", "nunique"),
            first_purchase=("invoicedate", "min"),
            last_purchase=("invoicedate", "max")
        )
        .reset_index()
    )

    customer["average_order_value"] = (
        customer["revenue"] / customer["orders"]
    )

    # Orders per observed calendar month is not calculated here;
    # this metric is orders per distinct product purchased.
    customer["orders_per_distinct_product"] = (
        customer["orders"] / customer["products"].replace(0, np.nan)
    )

    customer["customer_lifetime_days"] = (
        customer["last_purchase"] - customer["first_purchase"]
    ).dt.days

    return customer


def plot_customer_revenue_distribution(customers):
    if customers.empty:
        return

    plt.figure(figsize=(12, 6))
    sns.histplot(data=customers, x="revenue", bins=50)
    plt.title("Customer Revenue Distribution")
    plt.xlabel("Total Revenue per Customer")
    plt.ylabel("Number of Customers")
    plt.tight_layout()
    plt.savefig(
        FIGURE_DIR / "customer_revenue_distribution.png", dpi=200
    )
    plt.close()


# ------------------------------------------------------------
# 9. RFM CUSTOMER SEGMENTATION
# ------------------------------------------------------------

def calculate_rfm(df):
    """
    Recency: days since last purchase.
    Frequency: distinct invoices.
    Monetary: total retained sales revenue.
    """

    data = df.dropna(subset=["customerid"]).copy()

    if data.empty:
        return pd.DataFrame(columns=[
            "customerid", "recency", "frequency", "monetary",
            "r_score", "f_score", "m_score", "rfm_score"
        ])

    analysis_date = data["invoicedate"].max().normalize() + pd.Timedelta(days=1)

    rfm = (
        data.groupby("customerid")
        .agg(
            last_purchase=("invoicedate", "max"),
            frequency=("invoiceno", "nunique"),
            monetary=("revenue", "sum")
        )
        .reset_index()
    )

    rfm["recency"] = (
        analysis_date - rfm["last_purchase"].dt.normalize()
    ).dt.days

    rfm = rfm.drop(columns="last_purchase")

    # Rank-based quintiles handle tied values more robustly.
    # The percentile scores run from 1 (low) to 5 (high).
    def quintile_score(series, reverse=False):
        percentile = series.rank(method="average", pct=True)
        scores = np.ceil(percentile * 5).clip(1, 5).astype(int)
        return 6 - scores if reverse else scores

    rfm["r_score"] = quintile_score(rfm["recency"], reverse=True)
    rfm["f_score"] = quintile_score(rfm["frequency"])
    rfm["m_score"] = quintile_score(rfm["monetary"])

    rfm["rfm_score"] = (
        rfm["r_score"].astype(str)
        + rfm["f_score"].astype(str)
        + rfm["m_score"].astype(str)
    )

    return rfm


def assign_customer_segment(rfm):
    data = rfm.copy()

    if data.empty:
        data["segment"] = pd.Series(dtype="object")
        return data

    conditions = [
        (
            (data["r_score"] >= 4)
            & (data["f_score"] >= 4)
            & (data["m_score"] >= 4)
        ),
        (
            (data["r_score"] >= 3)
            & (data["f_score"] >= 4)
        ),
        (
            (data["r_score"] <= 2)
            & (data["f_score"] >= 3)
        ),
        (
            (data["r_score"] <= 2)
            & (data["f_score"] <= 2)
        )
    ]

    labels = [
        "Champions",
        "Loyal Customers",
        "At Risk",
        "Hibernating"
    ]

    data["segment"] = np.select(
        conditions, labels, default="Potential Loyalists"
    )

    return data

    # ------------------------------------------------------------
# 10. COUNTRY PERFORMANCE
# ------------------------------------------------------------

def country_performance(df, n=15):
    countries = (
        df.groupby("country")
        .agg(
            revenue=("revenue", "sum"),
            orders=("invoiceno", "nunique"),
            customers=("customerid", "nunique"),
            units=("quantity", "sum")
        )
        .reset_index()
    )

    countries["aov"] = (
        countries["revenue"] / countries["orders"]
    )

    return countries.sort_values(
        "revenue", ascending=False
    ).head(n).reset_index(drop=True)


# ------------------------------------------------------------
# 11. PRODUCT PRICING ANALYSIS
# ------------------------------------------------------------

def pricing_analysis(df):
    pricing = (
        df.groupby(["stockcode", "description"])
        .agg(
            average_price=("unitprice", "mean"),
            median_price=("unitprice", "median"),
            units_sold=("quantity", "sum"),
            revenue=("revenue", "sum"),
            orders=("invoiceno", "nunique")
        )
        .reset_index()
    )

    return pricing.sort_values(
        "revenue", ascending=False
    ).reset_index(drop=True)


# ------------------------------------------------------------
# 12. HOURLY SALES ANALYSIS
# ------------------------------------------------------------

def hourly_sales(df):
    hourly = (
        df.groupby("hour")
        .agg(
            revenue=("revenue", "sum"),
            orders=("invoiceno", "nunique"),
            units=("quantity", "sum")
        )
        .reset_index()
    )

    # Include all 24 hours, including hours without transactions.
    hourly = (
        hourly.set_index("hour")
        .reindex(range(24), fill_value=0)
        .rename_axis("hour")
        .reset_index()
    )

    return hourly


def plot_hourly_sales(hourly):
    if hourly.empty:
        return

    plt.figure(figsize=(12, 6))
    sns.lineplot(data=hourly, x="hour", y="revenue", marker="o")
    plt.title("Revenue by Hour of Day")
    plt.xlabel("Hour of Day")
    plt.ylabel("Revenue")
    plt.xticks(range(24))
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "hourly_revenue.png", dpi=200)
    plt.close()


# ------------------------------------------------------------
# 13. REUSABLE WORD REPORT TABLE
# ------------------------------------------------------------

def add_table_to_word(doc, dataframe, max_rows=15):
    """Insert a DataFrame as a readable Word table."""

    if dataframe is None or dataframe.empty:
        doc.add_paragraph("No data available for this section.")
        return

    display_df = dataframe.head(max_rows).copy()

    table = doc.add_table(rows=1, cols=len(display_df.columns))
    table.style = "Light Shading Accent 1"

    for index, column in enumerate(display_df.columns):
        table.rows[0].cells[index].text = str(column)

    for _, row in display_df.iterrows():
        cells = table.add_row().cells

        for index, value in enumerate(row):
            if pd.isna(value):
                text_value = "N/A"
            elif isinstance(value, (float, np.floating)):
                text_value = f"{value:,.2f}"
            else:
                text_value = str(value)

            cells[index].text = text_value

    doc.add_paragraph()


def add_chart_to_word(doc, filename, caption):
    """Insert a chart into the Word document if it exists."""

    path = FIGURE_DIR / filename

    if path.exists():
        doc.add_picture(str(path), width=Inches(6.0))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

        paragraph = doc.add_paragraph(caption)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


# ------------------------------------------------------------
# 14. HELPER FOR REPORT TEXT
# ------------------------------------------------------------

def money(value):
    """Format a numeric result for display."""

    if pd.isna(value):
        return "N/A"

    return f"{value:,.2f}"


def add_bullet(doc, text):
    doc.add_paragraph(text, style="List Bullet")

    # ------------------------------------------------------------
# 15. CREATE THE WORD REPORT
# ------------------------------------------------------------

def create_word_report(
    kpis,
    quality_report,
    monthly,
    products,
    customers,
    rfm,
    countries,
    pricing,
    hourly
):
    """Create a Word report containing analysis and interpretations."""

    doc = Document()

    # Document formatting.
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)

    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(9)

    title = doc.add_heading(
        "Online Retail Customer Analytics Report", level=0
    )
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    subtitle = doc.add_paragraph(
        "Sales Performance, Product Insights and Customer Behavior"
    )
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(
        "Purpose: To analyze historical retail transactions, "
        "identify customer and product patterns, and develop "
        "practical recommendations for business decision-making."
    )

    doc.add_paragraph(
        "Reporting note: Monetary values use the source dataset's "
        "currency. The currency is not inferred by this script."
    )

    # --------------------------------------------------------
    # 1. EXECUTIVE SUMMARY
    # --------------------------------------------------------

    doc.add_heading("1. Executive Summary", level=1)

    for name, value in kpis.items():
        add_bullet(doc, f"{name}: {money(value)}")

    if not monthly.empty:
        peak = monthly.loc[monthly["revenue"].idxmax()]
        doc.add_paragraph(
            f"Finding: The highest-revenue month was "
            f"{peak['year_month']}, with revenue of "
            f"{money(peak['revenue'])}."
        )

    if not products.empty:
        best_product = products.iloc[0]
        doc.add_paragraph(
            f"Finding: The leading product by revenue was "
            f"{best_product['description']}, generating "
            f"{money(best_product['revenue'])}."
        )

    if not countries.empty:
        best_country = countries.iloc[0]
        doc.add_paragraph(
            f"Finding: The leading country by revenue was "
            f"{best_country['country']}, with revenue of "
            f"{money(best_country['revenue'])}."
        )

    doc.add_paragraph(
        "Interpretation: Total revenue measures sales value "
        "in the retained records. Average order value estimates "
        "revenue per distinct invoice. These measures describe "
        "performance but do not, by themselves, measure profit."
    )

    # --------------------------------------------------------
    # 2. DATA QUALITY
    # --------------------------------------------------------

    doc.add_heading("2. Data Quality Assessment", level=1)

    add_table_to_word(doc, quality_report, max_rows=40)

    if not quality_report.empty:
        missing_columns = quality_report[
            quality_report["missing_count"] > 0
        ]

        doc.add_paragraph(
            f"{len(missing_columns)} columns contain missing values."
        )

        if not missing_columns.empty:
            most_missing = missing_columns.iloc[0]
            doc.add_paragraph(
                f"The highest missing-value percentage is in "
                f"'{most_missing['column']}' "
                f"({most_missing['missing_pct']:.2f}%). "
                "Review these missing values before relying on "
                "affected analyses."
            )

    doc.add_paragraph(
        "Interpretation: Missing customer IDs prevent some "
        "transactions from being attributed to known customers. "
        "The cleaning procedure also removes duplicate rows, "
        "invalid dates and records with non-positive quantities "
        "or unit prices."
    )

    # --------------------------------------------------------
    # 3. MONTHLY SALES
    # --------------------------------------------------------

    doc.add_heading("3. Monthly Sales Performance", level=1)

    add_table_to_word(doc, monthly, max_rows=36)

    add_chart_to_word(
        doc,
        "monthly_revenue.png",
        "Figure 1. Monthly revenue trend."
    )

    if not monthly.empty:
        peak = monthly.loc[monthly["revenue"].idxmax()]
        low = monthly.loc[monthly["revenue"].idxmin()]

        doc.add_paragraph(
            f"Interpretation: Revenue peaked in {peak['year_month']} "
            f"at {money(peak['revenue'])} and was lowest in "
            f"{low['year_month']} at {money(low['revenue'])}. "
            "Investigate seasonal demand, promotions and the "
            "number of trading days before attributing the "
            "difference to a particular cause."
        )

    # --------------------------------------------------------
    # 4. PRODUCT PERFORMANCE
    # --------------------------------------------------------

    doc.add_heading("4. Product Performance", level=1)

    add_table_to_word(doc, products, max_rows=15)

    add_chart_to_word(
        doc,
        "top_products_revenue.png",
        "Figure 2. Highest-revenue products."
    )

    if not products.empty:
        best = products.iloc[0]

        doc.add_paragraph(
            f"Interpretation: {best['description']} is the "
            f"highest-revenue product in the ranking, with "
            f"{money(best['revenue'])} in sales. Revenue share "
            "helps show how much each product contributes to "
            "the total revenue of the products in the full "
            "cleaned dataset."
        )

    # --------------------------------------------------------
    # 5. CUSTOMER ANALYSIS
    # --------------------------------------------------------

    doc.add_heading("5. Customer Analysis", level=1)

    doc.add_paragraph(
        f"The customer-level dataset contains "
        f"{len(customers):,} customers with an identifiable ID."
    )

    top_customers = customers.sort_values(
        "revenue", ascending=False
    )

    add_table_to_word(doc, top_customers, max_rows=15)

    add_chart_to_word(
        doc,
        "customer_revenue_distribution.png",
        "Figure 3. Distribution of customer revenue."
    )

    if not customers.empty:
        median_revenue = customers["revenue"].median()
        mean_revenue = customers["revenue"].mean()

        doc.add_paragraph(
            f"Average revenue per identified customer is "
            f"{money(mean_revenue)}, while median customer "
            f"revenue is {money(median_revenue)}. "
            "If the mean is substantially higher than the median, "
            "revenue may be concentrated among a smaller number "
            "of high-spending customers."
        )

    doc.add_paragraph(
        "Interpretation: Prioritize customer retention using "
        "multiple measures, including revenue, order frequency "
        "and purchase recency. Revenue alone does not establish "
        "customer profitability."
    )

    # --------------------------------------------------------
    # 6. RFM SEGMENTATION
    # --------------------------------------------------------

    doc.add_heading("6. RFM Customer Segmentation", level=1)

    if not rfm.empty:
        segment_counts = (
            rfm.groupby("segment")
            .size()
            .reset_index(name="customers")
            .sort_values("customers", ascending=False)
        )

        segment_counts["customer_share_pct"] = (
            segment_counts["customers"] / len(rfm) * 100
        )

        add_table_to_word(doc, segment_counts, max_rows=20)

        doc.add_paragraph(
            "Interpretation of RFM: Recency measures how recently "
            "a customer purchased, frequency counts distinct "
            "invoices, and monetary value measures retained sales."
        )

        add_bullet(
            doc,
            "Champions: customers scoring highly on recency, "
            "frequency and monetary value."
        )
        add_bullet(
            doc,
            "Loyal Customers: recently active customers with "
            "relatively frequent purchases."
        )
        add_bullet(
            doc,
            "At Risk: customers with older purchases but "
            "relatively high historical purchase frequency."
        )
        add_bullet(
            doc,
            "Hibernating: customers with older purchases and "
            "relatively low purchase frequency."
        )
        add_bullet(
            doc,
            "Potential Loyalists: customers not captured by "
            "the preceding rules."
        )
    else:
        doc.add_paragraph(
            "RFM segmentation could not be calculated because "
            "no identified customers remained in the data."
        )

    doc.add_paragraph(
        "Recommendation: Test segment-specific campaigns and "
        "measure conversion, repeat purchases and incremental "
        "revenue rather than assuming the campaigns will work."
    )

    # --------------------------------------------------------
    # 7. COUNTRY PERFORMANCE
    # --------------------------------------------------------

    doc.add_heading("7. Country Performance", level=1)

    add_table_to_word(doc, countries, max_rows=15)

    if not countries.empty:
        best = countries.iloc[0]

        doc.add_paragraph(
            f"Interpretation: {best['country']} ranks first among "
            f"the displayed countries by revenue, with "
            f"{money(best['revenue'])}. Compare order volume, "
            "customer count and average order value to understand "
            "differences in market size and spending behavior."
        )

    # --------------------------------------------------------
    # 8. PRODUCT PRICING
    # --------------------------------------------------------

    doc.add_heading("8. Product Pricing Analysis", level=1)

    add_table_to_word(doc, pricing, max_rows=15)

    doc.add_paragraph(
        "Interpretation: Average and median prices summarize "
        "observed transaction prices for each product. Units sold "
        "and revenue can help identify products with different "
        "sales patterns. This descriptive analysis cannot prove "
        "that a price change causes a change in demand."
    )

    # --------------------------------------------------------
    # 9. HOURLY SALES
    # --------------------------------------------------------

    doc.add_heading("9. Hourly Sales Behavior", level=1)

    add_table_to_word(doc, hourly, max_rows=24)

    add_chart_to_word(
        doc,
        "hourly_revenue.png",
        "Figure 4. Revenue by hour of day."
    )

    if not hourly.empty:
        peak_hour = hourly.loc[hourly["revenue"].idxmax()]

        doc.add_paragraph(
            f"Interpretation: The highest-revenue hour is "
            f"{int(peak_hour['hour']):02d}:00, with revenue of "
            f"{money(peak_hour['revenue'])}. Check whether this "
            "pattern holds across different days, months and "
            "seasons before making staffing decisions."
        )

    # --------------------------------------------------------
    # 10. BUSINESS RECOMMENDATIONS
    # --------------------------------------------------------

    doc.add_heading("10. Business Recommendations", level=1)

    recommendations = [
        "Monitor monthly revenue, orders and average order value "
        "to identify material changes in performance.",
        "Test retention campaigns for suitable RFM segments and "
        "measure the results against a control group where feasible.",
        "Use product revenue, unit volume and customer reach "
        "together when reviewing inventory priorities.",
        "Compare country revenue with order counts and average "
        "order value before allocating marketing resources.",
        "Review missing data, cancellations and returns before "
        "using the results for financial reporting.",
        "Use controlled experiments before making causal claims "
        "about price changes or promotional effectiveness."
    ]

    for recommendation in recommendations:
        add_bullet(doc, recommendation)

    # --------------------------------------------------------
    # 11. LIMITATIONS
    # --------------------------------------------------------

    doc.add_heading("11. Limitations and Definitions", level=1)

    doc.add_paragraph(
        "The report summarizes historical transactions after "
        "cleaning. It is descriptive, not a forecast or causal "
        "analysis. Non-positive quantities and prices are excluded, "
        "so revenue is not net revenue after returns or refunds. "
        "Costs, discounts, shipping and profit are not modeled "
        "unless those fields are separately supplied and analyzed."
    )

    doc.add_paragraph(
        "RFM scores are relative to the customers in this dataset. "
        "The analysis date is one day after the latest retained "
        "invoice date, so recency reflects the end of the observed "
        "period, not today's date."
    )

    # --------------------------------------------------------
    # SAVE WORD REPORT
    # --------------------------------------------------------

    report_path = OUTPUT_DIR / "Online_Retail_Analytics_Report.docx"

    doc.save(report_path)

    print(f"\nWord report saved to: {report_path.resolve()}")

    return report_path

    # ------------------------------------------------------------
# 16. MAIN PIPELINE
# ------------------------------------------------------------

def main():
    """Run the full analytics workflow from start to finish."""

    print("\n" + "=" * 60)
    print("ONLINE RETAIL CUSTOMER ANALYTICS")
    print("=" * 60)

    # 1. Load source data.
    raw_df = load_data()

    # 2. Profile data quality before cleaning.
    quality_report = profile_data(raw_df)

    quality_report.to_csv(
        TABLE_DIR / "data_quality_report.csv",
        index=False
    )

    print("\nDATA QUALITY REPORT")
    print(quality_report.to_string(index=False))

    # 3. Clean the data.
    df = clean_data(raw_df)

    # Save the cleaned transaction dataset.
    df.to_csv(
        TABLE_DIR / "cleaned_transactions.csv",
        index=False
    )

    # 4. Executive KPIs.
    kpis = calculate_kpis(df)

    print("\nEXECUTIVE KPIs")
    print(kpis.to_string())

    kpis.rename_axis("KPI").to_csv(
        TABLE_DIR / "executive_kpis.csv",
        header=["value"]
    )

    # 5. Monthly sales.
    monthly = monthly_sales(df)

    monthly.to_csv(
        TABLE_DIR / "monthly_sales.csv",
        index=False
    )

    plot_monthly_revenue(monthly)

    # 6. Product performance.
    products = top_products(df, n=20)

    products.to_csv(
        TABLE_DIR / "top_products.csv",
        index=False
    )

    plot_top_products(products)

    print("\nTOP PRODUCTS")
    print(products.head(10).to_string(index=False))

    # 7. Customer analysis.
    customers = customer_metrics(df)

    customers.to_csv(
        TABLE_DIR / "customer_metrics.csv",
        index=False
    )

    plot_customer_revenue_distribution(customers)

    # 8. RFM segmentation.
    rfm = calculate_rfm(df)
    rfm = assign_customer_segment(rfm)

    rfm.to_csv(
        TABLE_DIR / "customer_rfm_segments.csv",
        index=False
    )

    if not rfm.empty:
        print("\nCUSTOMER SEGMENTS")
        print(rfm["segment"].value_counts().to_string())

    # 9. Country performance.
    countries = country_performance(df, n=15)

    countries.to_csv(
        TABLE_DIR / "country_performance.csv",
        index=False
    )

    print("\nTOP COUNTRIES")
    print(countries.head(10).to_string(index=False))

    # 10. Product pricing.
    pricing = pricing_analysis(df)

    pricing.to_csv(
        TABLE_DIR / "product_pricing_analysis.csv",
        index=False
    )

    # 11. Hourly behavior.
    hourly = hourly_sales(df)

    hourly.to_csv(
        TABLE_DIR / "hourly_sales.csv",
        index=False
    )

    plot_hourly_sales(hourly)

    # 12. Generate the Word report after all results and charts
    # have been produced.
    report_path = create_word_report(
        kpis=kpis,
        quality_report=quality_report,
        monthly=monthly,
        products=products,
        customers=customers,
        rfm=rfm,
        countries=countries,
        pricing=pricing,
        hourly=hourly
    )

    # 13. Completion summary.
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    print(f"Cleaned data: {TABLE_DIR / 'cleaned_transactions.csv'}")
    print(f"CSV tables:   {TABLE_DIR.resolve()}")
    print(f"Charts:       {FIGURE_DIR.resolve()}")
    print(f"Word report:  {report_path.resolve()}")


# ------------------------------------------------------------
# 17. RUN THE SCRIPT
# ------------------------------------------------------------

if __name__ == "__main__":
    main()