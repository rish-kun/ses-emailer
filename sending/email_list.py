import pandas as pd

from sending.validation import is_valid_email, normalize_email


def _read_dataframe(file_path):
    """Read an Excel or CSV file into a DataFrame based on the file extension."""
    if str(file_path).lower().endswith(".csv"):
        return pd.read_csv(file_path)
    return pd.read_excel(file_path)


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
        df = _read_dataframe(file_path)
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


def scrape_excel_rows(file_path, email_column=0):
    """
    Read an Excel/CSV file into personalization rows.

    Each row becomes ``{"email": <address>, "fields": {<header>: <value>, ...}}``
    for rows whose email column holds a valid address. Field values are stringified;
    blank/NaN cells become empty strings. Duplicate emails keep the first row.

    Args:
        file_path (str): Path to the Excel/CSV file.
        email_column (int): 0-based index of the column holding email addresses.

    Returns:
        dict: ``{"headers": [...], "email_column": <name>, "rows": [...],
        "count": <int>}``.
    """
    try:
        df = _read_dataframe(file_path)
        headers = [str(c) for c in df.columns.tolist()]
        if not headers:
            return {"headers": [], "email_column": None, "rows": [], "count": 0}

        email_column = max(0, min(email_column, len(headers) - 1))
        email_header = headers[email_column]

        rows: list[dict] = []
        seen: set[str] = set()
        for _, record in df.iterrows():
            raw_email = record.iloc[email_column]
            if pd.isna(raw_email):
                continue
            email = normalize_email(raw_email)
            if not email or email in seen or not is_valid_email(email):
                continue
            seen.add(email)
            fields = {
                header: ("" if pd.isna(value) else str(value).strip())
                for header, value in zip(headers, record.tolist())
            }
            rows.append({"email": email, "fields": fields})

        return {
            "headers": headers,
            "email_column": email_header,
            "rows": rows,
            "count": len(rows),
        }
    except Exception as e:
        print(f"Error reading Excel rows: {e}")
        return {"headers": [], "email_column": None, "rows": [], "count": 0}
