import streamlit as st
import pandas as pd

st.title("📊 Flexible Mutual Fund vs Benchmark Comparison")

# Upload files
schemes_file = st.file_uploader("📄 Upload schemes.csv", type="csv")
benchmarks_file = st.file_uploader("📄 Upload benchmarks.csv", type="csv")

if schemes_file and benchmarks_file:
    schemes_df = pd.read_csv(schemes_file, skiprows=1, encoding="ISO-8859-1", low_memory=False)
    benchmarks_df = pd.read_csv(benchmarks_file, skiprows=2, encoding="ISO-8859-1", low_memory=False)

    st.subheader("🔧 Column Selection for Scheme File")
    scheme_cols = schemes_df.columns.tolist()

    scheme_name_col = st.selectbox("Scheme Name Column", scheme_cols)
    scheme_stock_col = st.selectbox("Stock Name Column", scheme_cols, index=4)
    scheme_weight_col = st.selectbox("Scheme Weight (%) Column", scheme_cols, index=9)

    scheme_list = schemes_df[scheme_name_col].dropna().unique()
    selected_scheme = st.selectbox("🔽 Select a Mutual Fund Scheme", scheme_list)

    filtered_scheme = schemes_df[schemes_df[scheme_name_col] == selected_scheme]

    st.subheader("🔧 Column Selection for Benchmark File")
    benchmark_cols = benchmarks_df.columns.tolist()

    benchmark_name = st.text_input("Enter Benchmark Name (e.g., BSE500)", value="BSE500")
    benchmark_filter_col = st.selectbox("Benchmark Name Column", benchmark_cols, index=3)
    benchmark_stock_col = st.selectbox("Benchmark Stock Name Column", benchmark_cols, index=4)
    benchmark_weight_col = st.selectbox("Benchmark Weight (%) Column", benchmark_cols, index=9)

    if not filtered_scheme.empty:
        # Scheme holdings
        scheme_holdings = filtered_scheme[[scheme_stock_col, scheme_weight_col]]
        scheme_holdings.columns = ['Stock', 'Scheme_Weight']
        scheme_holdings['Stock'] = scheme_holdings['Stock'].astype(str).str.upper()
        scheme_holdings['Scheme_Weight'] = pd.to_numeric(scheme_holdings['Scheme_Weight'], errors='coerce')

        # Benchmark holdings
        benchmark_filtered = benchmarks_df[benchmarks_df[benchmark_filter_col] == benchmark_name]
        benchmark_holdings = benchmark_filtered[[benchmark_stock_col, benchmark_weight_col]]
        benchmark_holdings.columns = ['Stock', 'Benchmark_Weight']
        benchmark_holdings['Stock'] = benchmark_holdings['Stock'].astype(str).str.upper()
        benchmark_holdings['Benchmark_Weight'] = pd.to_numeric(benchmark_holdings['Benchmark_Weight'], errors='coerce')

        # Merge and calculate
        merged = pd.merge(scheme_holdings, benchmark_holdings, on='Stock', how='outer').fillna(0)
        merged['Active_Weight'] = merged['Scheme_Weight'] - merged['Benchmark_Weight']

        # Results
        st.subheader("📉 Top 5 Underacquired Stocks")
        under = merged.sort_values(by='Active_Weight').head(5)
        st.dataframe(under[['Stock', 'Active_Weight']])

        st.subheader("📈 Top 5 Overacquired Stocks")
        over = merged.sort_values(by='Active_Weight').tail(5)
        st.dataframe(over[['Stock', 'Active_Weight']])

        # Download
        csv = merged.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Full CSV", data=csv, file_name="scheme_vs_benchmark_comparison.csv")
    else:
        st.warning("❌ No data found for the selected scheme.")
