"""
Adapter tests.

Requires: pip install "bogu[adapters]"
"""

import json

import pytest

from bogu import create_pipeline


@pytest.fixture
def pipeline():  # type: ignore[no-untyped-def]
    return create_pipeline("basic")


# ---------------------------------------------------------------------------
# DocumentAnonymizer
# ---------------------------------------------------------------------------

def test_txt_file(tmp_path, pipeline) -> None:  # type: ignore[no-untyped-def]
    from bogu.adapters.document import DocumentAnonymizer

    f = tmp_path / "test.txt"
    f.write_text("Contact alice@example.com or bob@test.org.", encoding="utf-8")

    da = DocumentAnonymizer(pipeline)
    result, em = da.anonymize_file(f)

    assert "alice@example.com" not in result
    assert "bob@test.org" not in result
    assert len(em) == 2


def test_txt_file_can_be_previewed(tmp_path, pipeline) -> None:  # type: ignore[no-untyped-def]
    from bogu.adapters.document import DocumentAnonymizer

    path = tmp_path / "input.txt"
    path.write_text("Email alice@example.com", encoding="utf-8")
    preview, em = DocumentAnonymizer(pipeline).preview_file(path)
    assert preview.redacted_text == "Email [EMAIL_1]"
    assert preview.categories == {"EMAIL": 1}
    assert len(em) == 1


def test_json_file(tmp_path, pipeline) -> None:  # type: ignore[no-untyped-def]
    from bogu.adapters.document import DocumentAnonymizer

    data = {"name": "Alice", "email": "alice@example.com", "age": 30}
    f = tmp_path / "data.json"
    f.write_text(json.dumps(data), encoding="utf-8")

    da = DocumentAnonymizer(pipeline)
    result, em = da.anonymize_file(f)

    assert "alice@example.com" not in result


def test_unsupported_extension_raises(tmp_path, pipeline) -> None:  # type: ignore[no-untyped-def]
    from bogu.adapters.document import DocumentAnonymizer

    f = tmp_path / "data.xlsx"
    f.write_bytes(b"fake")

    da = DocumentAnonymizer(pipeline)
    with pytest.raises(ValueError, match="Unsupported file type"):
        da.anonymize_file(f)


# ---------------------------------------------------------------------------
# DatasetAnonymizer
# ---------------------------------------------------------------------------

def test_dataframe_anonymize():  # type: ignore[no-untyped-def]
    pytest.importorskip("pandas")
    import pandas as pd

    from bogu.adapters.dataset import DatasetAnonymizer

    df = pd.DataFrame({
        "name": ["Alice Smith", "Bob Jones"],
        "email": ["alice@example.com", "bob@test.org"],
        "age": [30, 25],
    })

    da = DatasetAnonymizer(create_pipeline("basic"))
    result, em = da.anonymize_dataframe(df, columns=["email"])

    assert "alice@example.com" not in result["email"].values
    # Non-anonymized column should be unchanged
    assert list(result["age"]) == [30, 25]
    assert list(result["name"]) == ["Alice Smith", "Bob Jones"]


def test_dataframe_auto_detect_string_columns():  # type: ignore[no-untyped-def]
    pytest.importorskip("pandas")
    import pandas as pd

    from bogu.adapters.dataset import DatasetAnonymizer

    df = pd.DataFrame({
        "email": ["alice@example.com"],
        "score": [99.5],
    })

    da = DatasetAnonymizer(create_pipeline("basic"))
    result, em = da.anonymize_dataframe(df)  # no columns= specified

    assert "alice@example.com" not in result["email"].values
    assert result["score"][0] == 99.5  # numeric untouched


def test_csv_anonymize(tmp_path):  # type: ignore[no-untyped-def]
    pytest.importorskip("pandas")
    from bogu.adapters.dataset import DatasetAnonymizer

    csv_file = tmp_path / "users.csv"
    csv_file.write_text("name,email\nAlice,alice@example.com\nBob,bob@test.org\n")

    da = DatasetAnonymizer(create_pipeline("basic"))
    result, em = da.anonymize_csv(str(csv_file), columns=["email"])

    assert "alice@example.com" not in result["email"].values
    assert len(em) == 2


def test_invalid_column_raises():  # type: ignore[no-untyped-def]
    pytest.importorskip("pandas")
    import pandas as pd

    from bogu.adapters.dataset import DatasetAnonymizer

    df = pd.DataFrame({"email": ["alice@example.com"]})
    da = DatasetAnonymizer(create_pipeline("basic"))

    with pytest.raises(ValueError, match="not found"):
        da.anonymize_dataframe(df, columns=["nonexistent"])
