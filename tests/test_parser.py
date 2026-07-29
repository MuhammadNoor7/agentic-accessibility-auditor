"""Tests for src/parser.py: visibility extraction and MASC bounds-wrapper selection.

Covers the data-quality fix where hidden (visibility="gone" /
visible-to-user="False") elements were being treated identically to visible
ones, and the related MASC bounds-wrapper "last wins" bug that frequently
produced invalid (inverted) rects specifically for hidden elements.
"""

from __future__ import annotations

from lxml import etree

from src.parser import _get_hint, _is_visible, _parse_masc_bounds, parse_xml_tree


def _elem(xml: str) -> etree._Element:
    return etree.fromstring(xml.encode("utf-8"))


# --- _get_hint ---------------------------------------------------------------

def test_get_hint_reads_masc_text_hint_attribute() -> None:
    """MASC's real XML uses `text-hint`, not `hint`/`android:hint` — confirmed
    against real data-masc dumps, where `hint`/`android:hint` never appear at
    all. Missing this alias silently zeroed every MASC EditText's hint, which
    is why R20 (hint-only label) could never fire on real MASC data."""
    elem = _elem('<node class="android.widget.EditText" text-hint="Join the chat now" />')
    assert _get_hint(elem) == "Join the chat now"


def test_get_hint_prefers_hint_over_text_hint_when_both_present() -> None:
    elem = _elem('<node class="android.widget.EditText" hint="A" text-hint="B" />')
    assert _get_hint(elem) == "A"


# --- _is_visible -----------------------------------------------------------

def test_is_visible_defaults_true_without_visibility_attrs() -> None:
    """Real UIAutomator dumps don't carry visibility/visible-to-user at
    all — absence of both must default to visible, not hidden."""
    elem = _elem('<node class="android.widget.Button" clickable="true" />')
    assert _is_visible(elem) is True


def test_is_visible_false_for_visibility_gone() -> None:
    elem = _elem('<node class="android.widget.TextView" visibility="gone" />')
    assert _is_visible(elem) is False


def test_is_visible_false_for_not_visible_to_user() -> None:
    elem = _elem('<node class="android.widget.TextView" visible-to-user="False" />')
    assert _is_visible(elem) is False


def test_is_visible_true_when_visibility_is_visible() -> None:
    elem = _elem(
        '<node class="android.widget.TextView" visibility="visible" visible-to-user="True" />'
    )
    assert _is_visible(elem) is True


# --- _parse_masc_bounds ------------------------------------------------------

def test_masc_bounds_prefers_absolute_when_valid() -> None:
    """With two valid candidates (local, absolute), the later ('absolute')
    one must win — matching real screen position, needed by R04/R08/R17/R24."""
    elem = _elem(
        """
        <node class="android.widget.TextView">
          <wrapper><node value="android.widget.TextView" /></wrapper>
          <wrapper><node value="0" /><node value="0" /><node value="318" /><node value="196" /></wrapper>
          <wrapper><node value="0" /><node value="280" /><node value="318" /><node value="476" /></wrapper>
        </node>
        """
    )
    assert _parse_masc_bounds(elem) == [0, 280, 318, 476]


def test_masc_bounds_falls_back_to_local_when_absolute_invalid() -> None:
    """When the last ('absolute') candidate is an inverted rect (a known
    pattern on visibility=gone elements — e.g. [0, 476, -1439, 476], a
    negative-width rect), fall back to the earlier ('local') candidate
    rather than returning the garbage rect."""
    elem = _elem(
        """
        <node class="android.support.v7.widget.AppCompatTextView" visibility="gone">
          <wrapper><node value="android.widget.TextView" /></wrapper>
          <wrapper><node value="0" /><node value="0" /><node value="0" /><node value="0" /></wrapper>
          <wrapper><node value="0" /><node value="476" /><node value="-1439" /><node value="476" /></wrapper>
        </node>
        """
    )
    assert _parse_masc_bounds(elem) == [0, 0, 0, 0]


def test_masc_bounds_returns_last_candidate_when_all_invalid() -> None:
    """When every candidate is an inverted rect, still return the last one
    (rather than None) so callers get *a* value — R07 already exists
    downstream to flag zero/invalid-size components."""
    elem = _elem(
        """
        <node class="android.widget.TextView">
          <wrapper><node value="10" /><node value="10" /><node value="5" /><node value="10" /></wrapper>
          <wrapper><node value="0" /><node value="476" /><node value="-1439" /><node value="476" /></wrapper>
        </node>
        """
    )
    assert _parse_masc_bounds(elem) == [0, 476, -1439, 476]


def test_masc_bounds_handles_single_candidate() -> None:
    """A node with only one 4-number wrapper candidate must still work
    (not every node has the usual local+absolute pair)."""
    elem = _elem(
        """
        <node class="android.widget.TextView">
          <wrapper><node value="10" /><node value="20" /><node value="110" /><node value="60" /></wrapper>
        </node>
        """
    )
    assert _parse_masc_bounds(elem) == [10, 20, 110, 60]


def test_masc_bounds_returns_none_without_candidates() -> None:
    elem = _elem('<node class="android.widget.TextView"><wrapper><node value="None" /></wrapper></node>')
    assert _parse_masc_bounds(elem) is None


# --- end-to-end: parse_xml_tree wires `visible` onto every component -------

def test_parse_xml_tree_marks_gone_elements_not_visible() -> None:
    root = _elem(
        """
        <hierarchy>
          <node class="android.widget.FrameLayout" bounds="[0,0][1080,1920]">
            <node class="android.widget.Button" text="Visible" bounds="[0,0][200,100]" />
            <node class="android.widget.TextView" text="Hidden" visibility="gone"
                  visible-to-user="False" bounds="[0,0][0,0]" />
          </node>
        </hierarchy>
        """
    )
    components = parse_xml_tree(root)
    by_text = {c["text"]: c for c in components if c.get("text")}
    assert by_text["Visible"]["visible"] is True
    assert by_text["Hidden"]["visible"] is False
