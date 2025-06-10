import pandas as pd

# Load both CSV files
schemes_df = pd.read_csv("schemes.csv", skiprows=1, encoding="ISO-8859-1", low_memory=False)
benchmarks_df = pd.read_csv("benchmarks.csv", skiprows=3, encoding="ISO-8859-1")

# Select scheme (from dropdown ideally)
selected_scheme = "Templeton India Equity Income Fund(G)"

# Filter schemes for the selected one
filtered_scheme = schemes_df[schemes_df.iloc[:, 2].astype(str).str.strip() == selected_scheme]

# Exit if no match found
if filtered_scheme.empty:
    raise ValueError(f"No scheme found for '{selected_scheme}'")

# Get benchmark name from column 25 (index 24)
benchmark_name = filtered_scheme.iloc[0, 24]
benchmark_name = "NIFTY500"

# Prepare scheme holdings: Ticker (col 4), Holding % (col 10)
scheme_holdings = filtered_scheme[[schemes_df.columns[4], schemes_df.columns[9]]]
scheme_holdings.columns = ['Stock', 'Scheme_Weight']


# Convert scheme weight to numeric
scheme_holdings['Stock'] = scheme_holdings['Stock'].astype(str).str.upper()
scheme_holdings['Scheme_Weight'] = pd.to_numeric(scheme_holdings['Scheme_Weight'], errors='coerce')

# Prepare benchmark holdings: Stock (col 4), Weight (col 10), filtered by benchmark name (col 6)
benchmark_filtered = benchmarks_df[benchmarks_df.iloc[:, 4] == benchmark_name]
benchmark_holdings = benchmark_filtered[[benchmarks_df.columns[3], benchmarks_df.columns[9]]]
benchmark_holdings.columns = ['Stock', 'Benchmark_Weight']

# Convert benchmark weight to numeric
benchmark_holdings['Benchmark_Weight'] = pd.to_numeric(benchmark_holdings['Benchmark_Weight'], errors='coerce')

# Merge and calculate Active Weight
merged = pd.merge(scheme_holdings, benchmark_holdings, on='Stock', how='outer').fillna(0)
merged['Active_Weight'] = merged['Scheme_Weight'] - merged['Benchmark_Weight']

# Sort and display
print("\nTop 5 Underacquired Stocks:")
print(merged.sort_values(by='Active_Weight').head(5)[['Stock', 'Active_Weight']])

print("\nTop 5 Overacquired Stocks:")
print(merged.sort_values(by='Active_Weight').tail(5)[['Stock', 'Active_Weight']])