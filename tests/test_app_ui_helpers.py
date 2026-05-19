from aventyr_ops.app import _current_selection_value
from aventyr_ops.ui.components import _safe


def test_current_selection_value_only_returns_matching_result():
    result = {"site": "Site Bravo"}

    assert _current_selection_value("INC-SAMPLE-1", "INC-SAMPLE-1", result) == result
    assert _current_selection_value("INC-SAMPLE-3", "INC-SAMPLE-1", result) is None
    assert _current_selection_value("INC-SAMPLE-3", None, result) is None


def test_safe_escapes_dynamic_html():
    assert _safe("<script>alert('x')</script>") == "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;"
