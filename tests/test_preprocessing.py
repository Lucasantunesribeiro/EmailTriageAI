from app.utils.preprocessing import preprocess_text


def test_preprocess_text_basic() -> None:
    text = "Ola, obrigado pelo retorno."
    result = preprocess_text(text)
    assert isinstance(result["clean_text"], str)
    assert isinstance(result["tokens"], list)
    assert result["stats"]["num_chars"] == len(text)
