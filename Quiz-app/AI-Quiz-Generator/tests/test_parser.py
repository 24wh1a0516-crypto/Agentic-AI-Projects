from app.ppt_parser import extract_text_from_ppt


def test_extract_text_from_ppt_requires_existing_file():
    try:
        extract_text_from_ppt("missing.pptx")
    except FileNotFoundError:
        assert True
    else:
        assert False
