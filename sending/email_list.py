import pandas as pd


def scrape_excel_column(file_path, column_index=6):
    """
    Scrape the 7th column (index 6) from an Excel file and return as a list.

    Args:
        file_path (str): Path to the Excel file
        column_index (int): Column index (0-based, default is 6 for 7th column)

    Returns:
        list: Values from the specified column
    """
    try:
        df = pd.read_excel(file_path)
        column_data = df.iloc[:, column_index].tolist()
        column_data = [
            item for item in column_data if (pd.notna(item) and item[0] != " ")
        ]
        return column_data

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []
