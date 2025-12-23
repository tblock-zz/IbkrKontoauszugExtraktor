import pandas as pd
import os
#--------------------------------------------------------------------------------------------------------------------
def exportToCsv(filename: str, dataFrames: dict):
    """
    Exports a dictionary of DataFrames to a single CSV file.
    dataFrames: dict where key is the section title and value is the DataFrame
    """
    # Remove file if exists to start fresh
    if os.path.exists(filename):
        os.remove(filename)

    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        for title, df in dataFrames.items():
            f.write(f"\n{title}\n")
            f.write("-" * 80 + "\n")
            # Write DataFrame to buffer
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_csv(f, index=False)
            elif isinstance(df, (int, float, str)):
                 f.write(f"{df}\n")
            else:
                f.write("No data\n")
            f.write("\n")
