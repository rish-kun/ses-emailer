from sending.personalize import extract_fields, has_tokens, missing_fields, render


def test_extract_fields_unique_in_order():
    assert extract_fields("Hi {{name}}", "Your seat {{ seat }} — {{name}}") == [
        "name",
        "seat",
    ]


def test_has_tokens():
    assert has_tokens("Hello {{name}}")
    assert not has_tokens("Hello there", "no tokens here")


def test_render_substitutes_case_insensitively():
    assert render("Hi {{Name}}!", {"name": "Alice"}) == "Hi Alice!"
    assert render("{{a}}-{{b}}", {"a": 1, "b": 2}) == "1-2"


def test_render_unknown_token_becomes_blank():
    assert render("Hi {{name}}, seat {{seat}}", {"name": "Bob"}) == "Hi Bob, seat "


def test_render_handles_empty_template():
    assert render("", {"name": "x"}) == ""


def test_missing_fields_reports_absent_or_blank():
    assert missing_fields({"name": "Bob", "seat": ""}, ["name", "seat"]) == ["seat"]
    assert missing_fields({"name": "Bob"}, ["name"]) == []
