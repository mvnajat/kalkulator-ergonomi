"""Keep Streamlit data editor input stable while a worksheet is open."""

from typing import Any, Callable, MutableMapping

import pandas as pd


def prepare_editor_scope(state: MutableMapping[str, Any], scope: str) -> None:
    """Start fresh editors when the user changes pages or worksheets.

    The previous worksheet's edited rows are already stored in its module data.
    A new scope therefore takes its baseline from those saved values.
    """
    if state.get("_table_editor_scope") != scope:
        state["_table_editor_scope"] = scope
        state["_table_editor_bases"] = {}
        state["_table_editor_revision"] = state.get("_table_editor_revision", 0) + 1


def edit_table_rows(
    state: MutableMapping[str, Any],
    rows: list[dict],
    editor_key: str,
    render_editor: Callable[..., pd.DataFrame],
    **editor_options: Any,
) -> list[dict]:
    """Render a table without feeding its edited output back as widget input.

    Streamlit tracks edits relative to the original dataframe. Replacing that
    dataframe with the previous editor result on every rerun can make the first
    cell edit disappear. Keep the source unchanged until the worksheet changes.
    """
    bases = state.setdefault("_table_editor_bases", {})
    if editor_key not in bases:
        bases[editor_key] = pd.DataFrame(rows).copy(deep=True)

    revision = state.get("_table_editor_revision", 0)
    edited = render_editor(
        bases[editor_key],
        key=f"{editor_key}_r{revision}",
        **editor_options,
    )
    return edited.to_dict("records")
