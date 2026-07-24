import pandas as pd

from sending.email_list import scrape_excel_column, scrape_excel_rows


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


def test_scrape_rows_returns_headers_and_fields(tmp_path):
    xlsx = tmp_path / "people.xlsx"
    pd.DataFrame(
        {"email": ["a@x.com", "bad", "b@y.io"], "name": ["Alice", "Nope", "Bob"], "seat": [1, 2, 3]}
    ).to_excel(xlsx, index=False)

    result = scrape_excel_rows(str(xlsx), email_column=0)
    assert result["headers"] == ["email", "name", "seat"]
    assert result["email_column"] == "email"
    assert result["count"] == 2  # invalid "bad" row dropped
    assert result["rows"][0] == {
        "email": "a@x.com",
        "fields": {"email": "a@x.com", "name": "Alice", "seat": "1"},
    }
    assert result["rows"][1]["fields"]["name"] == "Bob"


def test_scrape_rows_handles_non_email_column(tmp_path):
    csv = tmp_path / "people.csv"
    csv.write_text("name,email\nAlice,a@x.com\nBob,b@y.io\n")
    result = scrape_excel_rows(str(csv), email_column=1)
    assert result["email_column"] == "email"
    assert [r["email"] for r in result["rows"]] == ["a@x.com", "b@y.io"]
