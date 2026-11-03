import pytest

from backend.app.services.analyzer_service import analyze_code


def test_unused_import():
    code = "import os\n"

    issues = analyze_code(code)

    assert any(issue["code"] == "F401" for issue in issues)


def test_valid_code():
    code = "print('Hello World')\n"

    issues = analyze_code(code)

    assert issues == []


def test_empty_code():
    with pytest.raises(ValueError):
        analyze_code("   ")