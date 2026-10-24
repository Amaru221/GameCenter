from gamecenter.core import vdf

import pytest


def test_reads_simple_pairs() -> None:
    assert vdf.parse('"a" "1" "b" "two"') == {"a": "1", "b": "two"}


def test_reads_nested_blocks_and_comments() -> None:
    document = """
    // top-level comment
    "root"
    {
        "name"  "Half-Life 2"   // trailing comment
        "child" { "x" "1" }
    }
    """
    tree = vdf.parse(document)
    assert tree["root"]["name"] == "Half-Life 2"
    assert tree["root"]["child"] == {"x": "1"}


def test_unescapes_quotes_and_backslashes() -> None:
    tree = vdf.parse(r'"path" "C:\\Games\\Steam" "quote" "a\"b"')
    assert tree["path"] == r"C:\Games\Steam"
    assert tree["quote"] == 'a"b'


def test_accepts_bare_tokens() -> None:
    assert vdf.parse("key value") == {"key": "value"}


def test_get_is_case_insensitive() -> None:
    tree = vdf.parse('"Root" { "AppId" "220" }')
    assert vdf.get(tree["Root"], "appid") == "220"
    assert vdf.get(tree["Root"], "missing", "fallback") == "fallback"


def test_get_block_is_case_insensitive() -> None:
    tree = vdf.parse('"ROOT" { "Child" { "x" "1" } }')
    block = vdf.get_block(tree, "root")
    assert block is not None
    assert vdf.get_block(block, "child") == {"x": "1"}


def test_unterminated_string_is_rejected() -> None:
    with pytest.raises(vdf.VdfError):
        vdf.parse('"a" "b')


def test_unclosed_block_is_rejected() -> None:
    with pytest.raises(vdf.VdfError):
        vdf.parse('a { b "c"')


def test_key_without_value_is_rejected() -> None:
    with pytest.raises(vdf.VdfError):
        vdf.parse('"a"')
