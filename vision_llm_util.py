import os
import base64
import openai
from typing import List, Dict, Any

# Helper to encode image to base64 for API

def encode_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def extract_structured_data_from_image(image_path: str, prompt: str, model: str = None, max_tokens: int = 1024) -> Dict[str, Any]:
    """
    Send an image to a vision-capable LLM (e.g., GPT-4 Vision) and extract structured data as JSON.
    """
    model = model or os.getenv("OPENAI_VISION_MODEL", "gpt-4-vision-preview")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment.")
    openai.api_key = api_key
    image_b64 = encode_image_base64(image_path)
    messages = [
        {"role": "system", "content": "You are a document extraction assistant. Return JSON only."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": f"data:image/png;base64,{image_b64}"}
        ]}
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens
    )
    content = response.choices[0].message["content"]
    return content
