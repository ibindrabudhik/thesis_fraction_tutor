"""
Cheat-detection component: detects tab/window switches and shows a popup warning.

Uses a proper bidirectional Streamlit component (declare_component) so the
iframe gets `allow-same-origin` in its sandbox and can access the parent page.
"""

import os
import streamlit.components.v1 as components

# Declare the component – points to the directory containing index.html
_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cheat_detector")
_cheat_detector = components.declare_component("cheat_detector", path=_COMPONENT_DIR)


def render_tab_detector(key: str = "cheat_detector", reset_count: int = 0) -> int:
    """
    Render the invisible tab/window switch detector.

    Args:
        key: Streamlit component key.
        reset_count: Incremented each time the counter should be reset
                     (e.g. when moving to the next problem).

    Returns:
        int – number of times the student has switched away from the tab.
    """
    count = _cheat_detector(key=key, default=0, reset_count=reset_count)
    if count is None:
        count = 0
    return int(count)
