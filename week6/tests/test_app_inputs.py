# test_app_inputs.py
# Headless Streamlit tests (streamlit.testing.v1.AppTest) for the sidebar's
# feature-input options. No Groq API key or network is needed: manual selection
# uses the Route Builder only.

import os
import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = os.path.join(os.path.dirname(__file__), "..", "app.py")


def _app():
    return AppTest.from_file(APP, default_timeout=120).run()


# Test 1: Both input methods are offered, and manual selection is the default
def test_both_input_methods_offered_manual_default():
    at = _app()
    assert not at.exception
    radio = next(r for r in at.sidebar.radio if "specify features" in r.label)
    assert any("Upload" in o for o in radio.options)
    assert any("Manual" in o for o in radio.options)
    assert "Manual" in radio.value
    # manual mode shows the feature multiselect, pre-filled with Hole and Slot
    ms = next(m for m in at.sidebar.multiselect if "Select features" in m.label)
    assert ms.value == ["Hole", "Slot"]


# Test 2: A plan can be generated from manually selected features
def test_manual_selection_generates_plan():
    at = _app()
    next(m for m in at.sidebar.multiselect if "Select features" in m.label).set_value(["Hole", "Slot", "Thread"])
    gen = next(b for b in at.sidebar.button if "Generate" in b.label)
    gen.click()
    at.run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "Facing" in text and "Inspection" in text


# Test 3: Switching to image upload shows the uploader and hides manual selection
def test_switching_to_upload_hides_manual_multiselect():
    at = _app()
    radio = next(r for r in at.sidebar.radio if "specify features" in r.label)
    radio.set_value(next(o for o in radio.options if "Upload" in o))
    at.run()
    assert not at.exception
    assert not any("Select features" in m.label for m in at.sidebar.multiselect)
