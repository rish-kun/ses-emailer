from sending.validation import is_valid_email, normalize_email, partition_valid


def test_is_valid_email_accepts_normal_addresses():
    assert is_valid_email("alice@example.com")
    assert is_valid_email("  Bob.Smith@Sub.Example.CO  ")


def test_is_valid_email_rejects_junk():
    assert not is_valid_email("not-an-email")
    assert not is_valid_email("missing@domain")  # no TLD dot
    assert not is_valid_email("two @spaces.com")
    assert not is_valid_email("")
    assert not is_valid_email(12345)  # numeric cell, must not crash


def test_normalize_lowercases_and_strips():
    assert normalize_email("  Foo@BAR.com ") == "foo@bar.com"


def test_partition_valid_splits_and_dedupes():
    valid, invalid = partition_valid(
        ["a@x.com", "A@X.com", "junk", "", "b@y.io", 999]
    )
    assert valid == ["a@x.com", "b@y.io"]  # deduped, order preserved
    assert invalid == ["junk", "999"]
