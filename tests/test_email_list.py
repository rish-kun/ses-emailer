import pandas as pd

from sending.email_list import scrape_excel_column


def test_scrape_reads_valid_emails(tmp_path):
    xlsx = tmp_path / "list.xlsx"
    pd.DataFrame({"email": ["a@x.com", "b@y.io"]}).to_excel(xlsx, index=False)
    assert scrape_excel_column(str(xlsx), 0) == ["a@x.com", "b@y.io"]


def test_scrape_tolerates_numeric_and_blank_cells(tmp_path):
    """Regression: numeric/NaN cells previously crashed the parser (item[0])."""
    xlsx = tmp_path / "mixed.xlsx"
    pd.DataFrame({"col": [123, None, "keep@x.com", "not-an-email", "  "]}).to_excel(
        xlsx, index=False
    )
    assert scrape_excel_column(str(xlsx), 0) == ["keep@x.com"]


def test_scrape_dedupes_case_insensitively(tmp_path):
    xlsx = tmp_path / "dupes.xlsx"
    pd.DataFrame({"col": ["Dup@X.com", "dup@x.com", "u@y.io"]}).to_excel(
        xlsx, index=False
    )
    assert scrape_excel_column(str(xlsx), 0) == ["dup@x.com", "u@y.io"]


def test_scrape_reads_csv(tmp_path):
    csv = tmp_path / "list.csv"
    csv.write_text("email\nc@z.com\nbad\n")
    assert scrape_excel_column(str(csv), 0) == ["c@z.com"]
