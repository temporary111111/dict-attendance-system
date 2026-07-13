from pathlib import Path


def test_commenting_guidelines_document_the_project_style():
    guidelines = Path("../docs/commenting-guidelines.md").read_text(encoding="utf-8")

    assert "Taglish comments" in guidelines
    assert "business rules" in guidelines
    assert "Huwag i-comment ang obvious syntax" in guidelines
