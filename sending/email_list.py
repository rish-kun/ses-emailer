import pandas as pd

from sending.validation import is_valid_email, normalize_email


def scrape_excel_column(file_path, column_index=0):
    """
    Read a single column from an Excel/CSV file and return valid email addresses.

    Values are coerced to strings, trimmed/lowercased, filtered to valid emails,
    and de-duplicated (first-seen order preserved). This tolerates numeric or
    blank cells that previously crashed the parser.

    Args:
        file_path (str): Path to the Excel (.xlsx/.xls) or CSV file.
        column_index (int): 0-based column index to read (default 0).

    Returns:
        list[str]: Valid, de-duplicated email addresses from the column.
    """
    try:
        if str(file_path).lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)

        column_data = df.iloc[:, column_index].tolist()

        emails: list[str] = []
        seen: set[str] = set()
        for item in column_data:
            if pd.isna(item):
                continue
            email = normalize_email(item)
            if not email or email in seen:
                continue
            if is_valid_email(email):
                seen.add(email)
                emails.append(email)
        return emails

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []
