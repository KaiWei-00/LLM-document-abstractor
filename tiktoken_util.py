import tiktoken

def count_tokens(text: str, model: str = "gpt-3.5-turbo-instruct") -> int:
    """
    Count tokens in a string for a given OpenAI model.
    """
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))
