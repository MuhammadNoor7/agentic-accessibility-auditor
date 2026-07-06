"""Tests for extended parser fields used by R13-R20."""

from __future__ import annotations

from pathlib import Path

from src.parser import load_xml_root, parse_xml_tree

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "rules"


def test_parser_emits_extended_fields_on_fixture() -> None:
    xml_path = FIXTURES_DIR / "r05_unlabeled_input_fail.xml"
    components = parse_xml_tree(load_xml_root(xml_path))
    assert components
    component = components[0]
    for key in (
        "focus_order",
        "parent_id",
        "long_clickable",
        "scrollable",
        "selected",
        "checked",
        "password",
        "text_all_caps",
        "input_type",
        "important_for_accessibility",
        "media_type",
        "is_dialog",
        "label_for",
    ):
        assert key in component
    assert component["focus_order"] == 1


def test_parser_preserves_parent_id_hierarchy() -> None:
    xml_path = FIXTURES_DIR / "r01_missing_label_fail.xml"
    components = parse_xml_tree(load_xml_root(xml_path))
    child_with_parent = next(
        (component for component in components if component.get("parent_id")),
        None,
    )
    assert child_with_parent is not None
    parent = next(
        component
        for component in components
        if component["component_id"] == child_with_parent["parent_id"]
    )
    assert parent is not None


def test_parser_extracts_masc_nodes_from_wrapper_nesting() -> None:
    masc_xml = (
        Path(__file__).resolve().parents[1] / "data" / "data-masc" / "xml" / "chat" / "1054.xml"
    )
    if not masc_xml.is_file():
        import pytest

        pytest.skip("MASC XML not available (link data/data-masc/xml)")
    components = parse_xml_tree(load_xml_root(masc_xml))
    assert len(components) > 20
    assert all("focus_order" in component for component in components)
    assert any(component.get("text") for component in components)
