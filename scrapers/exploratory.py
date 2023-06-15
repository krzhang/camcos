from camcos.simulations.settings import DATA_PATH
import pandas as pd

# Load the CSV
### NOTE: If you want to have both the datasets of this year and last year,
# kindly rename the CSV file to the name from scraper.py
# e.g. transactionData.csv -> transactionData2023.csv
df = pd.read_csv(str(DATA_PATH / "transactionData.csv"))

# Filter the dataframe
filtered_df = df[df['callDataUsage'].isin([64, 0, 608, 64, 204])]

# Limit each value to at most 5 each
filtered_df = filtered_df.groupby('callDataUsage').head(5)

# Save the filtered data to a new CSV file
filtered_df.to_csv(str(DATA_PATH / "filteredTransactionData.csv"), index=False)