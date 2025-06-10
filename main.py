import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(layout="wide", page_title="Mutual Fund Benchmark Analyzer")
st.title("📊 Mutual Fund vs Benchmark Analyzer")
st.markdown("Upload `schemes.csv` and `benchmarks.csv` to get started.")

# File uploaders
schemes_file = st.file_uploader("Upload schemes.csv", type="csv")
benchmarks_file = st.file_uploader("Upload benchmarks.csv", type="csv")

# Function to match columns using regex
def find_column(possible_patterns, columns):
    for col in columns:
        for pattern in possible_patterns:
            if re.search(pattern, col, re.IGNORECASE):
                return col
    return None

if schemes_file and benchmarks_file:
    # Read CSVs
    schemes_df = pd.read_csv(schemes_file, encoding='ISO-8859-1', skiprows=1)
    benchmarks_df = pd.read_csv(benchmarks_file, encoding='ISO-8859-1', skiprows=2)

    # Get actual column names
    actual_cols = schemes_df.columns.tolist()

    # Find key columns
    scheme_col = find_column(["scheme"], actual_cols)
    stock_col = find_column(["security", "stock"], actual_cols)
    industry_col = find_column(["industry"], actual_cols)
    fund_weight_col = find_column(["% of holdings", "fund weight", "scheme weight"], actual_cols)
    benchmark_weight_col = find_column(["benchmark weight", "index weight", "nifty weight"], actual_cols)
    active_weight_col = find_column(["active weight"], actual_cols)

    # Error handling if any column is not found
    missing = []
    if not scheme_col: missing.append("Scheme Name")
    if not stock_col: missing.append("Stock Name")
    if not industry_col: missing.append("Industry")
    if not fund_weight_col: missing.append("Fund Weight")
    if not benchmark_weight_col: missing.append("Benchmark Weight")
    if not active_weight_col: missing.append("Active Weight")

    if missing:
        st.error(f"❌ Missing columns in your CSV: {', '.join(missing)}")
        st.write("Detected columns:", actual_cols)
        st.stop()

    # Rename columns
    schemes_df = schemes_df.rename(columns={
        scheme_col: 'Scheme Name',
        stock_col: 'Stock Name',
        industry_col: 'Industry',
        fund_weight_col: 'Fund Weight',
        benchmark_weight_col: 'Benchmark Weight',
        active_weight_col: 'Active Weight'
    })

    # Convert weight columns to numeric
    for col in ['Fund Weight', 'Benchmark Weight', 'Active Weight']:
        schemes_df[col] = pd.to_numeric(schemes_df[col], errors='coerce')

    # Drop missing essentials
    schemes_df = schemes_df.dropna(subset=['Scheme Name', 'Stock Name', 'Industry'])

    # Dropdown for scheme
    scheme_names = schemes_df['Scheme Name'].dropna().unique()
    selected_scheme = st.selectbox("Select a Scheme", scheme_names)

    filtered = schemes_df[schemes_df['Scheme Name'] == selected_scheme]

    # Group by Industry
    industry_fund = filtered.groupby('Industry')['Fund Weight'].sum().reset_index()
    industry_benchmark = filtered.groupby('Industry')['Benchmark Weight'].sum().reset_index()
    industry_summary = pd.merge(industry_fund, industry_benchmark, on='Industry', how='outer').fillna(0)
    industry_summary['Active Weight'] = industry_summary['Fund Weight'] - industry_summary['Benchmark Weight']

    # Top 10 Overweight & Underweight Stocks
    top_over = filtered.sort_values('Active Weight', ascending=False).dropna(subset=['Active Weight']).head(10)
    top_under = filtered.sort_values('Active Weight', ascending=True).dropna(subset=['Active Weight']).head(10)

    # Display summary
    st.subheader("📘 Industry-wise Summary")
    st.dataframe(industry_summary)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🟩 Top 10 Overweight Stocks")
        st.dataframe(top_over[['Stock Name', 'Active Weight']])
    with col2:
        st.subheader("🟥 Top 10 Underweight Stocks")
        st.dataframe(top_under[['Stock Name', 'Active Weight']])

    # Download Excel Report
    def to_excel():
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            industry_summary.to_excel(writer, index=False, sheet_name='Industry Summary')
            top_over.to_excel(writer, index=False, sheet_name='Top Overweight')
            top_under.to_excel(writer, index=False, sheet_name='Top Underweight')
        output.seek(0)
        return output

    st.download_button("📥 Download Excel Report", data=to_excel(),
                       file_name="Mutual_Fund_Report.xlsx", mime="application/vnd.ms-excel")

else:
    st.info("Please upload both files to begin analysis.")
