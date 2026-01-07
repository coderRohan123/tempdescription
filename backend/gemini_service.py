import os
import io
import base64
from typing import List, Dict, Tuple
from PIL import Image, ImageOps
from dotenv import load_dotenv

# Optional: uncomment if you still want to force certifi bundle globally.
# import certifi
# os.environ["SSL_CERT_FILE"] = certifi.where()
# os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
# os.environ["CURL_CA_BUNDLE"] = certifi.where()

import google.generativeai as genai

# -------------------------
# Setup
# -------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY/GOOGLE_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# Create model once
_model = genai.GenerativeModel(GEMINI_MODEL)

ALLOWED_MIME = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

# -------------------------
# Core Helpers
# -------------------------
def build_prompt(product_name: str, product_category: str, target_audience: str,
                 user_description: str, target_language: str) -> str:
    """Build the prompt text from product details."""
    parts = []
    if product_name:
        parts.append(f"Product Name: {product_name}")
    if product_category:
        parts.append(f"Category: {product_category}")
    if target_audience:
        parts.append(f"Target Audience: {target_audience}")
    if user_description:
        parts.append(f"Description: {user_description}")

    text_input = " | ".join(parts) if parts else ""
    language_instruction = (
        f"Provide the response in {target_language}."
        if target_language and target_language.lower() != "english"
        else ""
    )
    system_instruction = (
        "You are an expert marketing assistant. Create well-crafted, clean, and "
        "professional product descriptions that are focused and concise but comprehensive. "
        "Provide the content in clean paragraphs without markdown syntax (no # headers, "
        "no * bullet points). Use plain text formatting with clear line breaks between "
        "sections. Avoid generic phrases and focus on the specific product details provided."
    )
    prompt_text = (
        f"{system_instruction} {language_instruction} Based on this information: {text_input}. "
        "Include brand name, product category, target audience, key features, benefits, and "
        "usage instructions if mentioned. Keep it concise but comprehensive."
    )
    return prompt_text


def _load_image_from_base64(img_data: str) -> Tuple[Image.Image, str]:
    """
    Accepts base64 string that may be plain base64 or data URL (data:image/xxx;base64,...).
    Returns a PIL.Image and MIME type (best effort).
    """
    mime_type = None
    base64_data = img_data

    if isinstance(img_data, str) and img_data.startswith("data:image"):
        mime_type = img_data.split(";")[0].split(":")[1]
        base64_data = img_data.split(",")[1]

    image_bytes = base64.b64decode(base64_data)
    buf = io.BytesIO(image_bytes)
    img = Image.open(buf)

    # Normalize orientation and color space
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    # Best-effort MIME inference if not present
    fmt_to_mime = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "GIF": "image/gif",
        "WEBP": "image/webp",
    }
    if not mime_type:
        mime_type = fmt_to_mime.get(img.format or "PNG", "image/png")

    return img, mime_type


def _lang_instruction(lang: str) -> str:
    lang = (lang or "English").strip()
    return (
        f"You are an assistant that must respond in {lang}. "
        f"Write naturally and correctly in {lang}. Do not switch languages."
    )


# -------------------------
# Generation (Text-only)
# -------------------------
def generate_description_text_only(prompt_text: str) -> str:
    if not prompt_text:
        raise ValueError("Prompt text is required.")
    try:
        resp = _model.generate_content(prompt_text)
        if not resp or not getattr(resp, "text", None):
            raise ValueError("No response from AI model. Please try again.")
        return resp.text
    except Exception as e:
        _raise_friendly_gemini_error(e)


# -------------------------
# Generation (With Images)
# -------------------------
def generate_description_with_images(prompt_text: str, image_list: List[str]) -> str:
    if not prompt_text:
        raise ValueError("Prompt text is required.")
    if not image_list or len(image_list) == 0:
        raise ValueError("At least one image is required.")
    if len(image_list) > 5:
        raise ValueError("Maximum 5 images allowed.")

    try:
        inputs = [_lang_instruction("English"), prompt_text]
        for img_data in image_list:
            pil_img, _mime = _load_image_from_base64(img_data)
            inputs.append(pil_img)

        resp = _model.generate_content(inputs)
        if not resp or not getattr(resp, "text", None):
            raise ValueError("No response from AI model. Please try again.")
        return resp.text
    except Exception as e:
        _raise_friendly_gemini_error(e)


# -------------------------
# Orchestrator
# -------------------------
def generate_product_description(
    product_name: str,
    product_category: str,
    target_audience: str,
    user_description: str,
    target_language: str,
    images: List[str] = None,
) -> str:
    prompt_text = build_prompt(
        product_name, product_category, target_audience, user_description, target_language
    )

    if images and len(images) > 0:
        return generate_description_with_images(prompt_text, images)
    else:
        return generate_description_text_only(prompt_text)


# -------------------------
# Translation
# -------------------------
def translate_description(description: str, target_languages: List[str]) -> Dict[str, str]:
    if not description:
        raise ValueError("Description is required")
    if not target_languages or len(target_languages) == 0:
        raise ValueError("At least one target language is required")
    if len(target_languages) > 3:
        raise ValueError("Maximum 3 languages allowed")

    translations: Dict[str, str] = {}
    try:
        for lang in target_languages:
            lang = (lang or "").strip()
            if not lang:
                continue

            prompt = (
                f"{_lang_instruction(lang)}\n\n"
                "Translate the following product description. "
                "Maintain the same professional tone, structure, and formatting. "
                "Do not add or remove any information. Just translate the text accurately.\n\n"
                f"Product Description:\n{description}\n\n"
                f"Translated to {lang}:"
            )
            resp = _model.generate_content(prompt)
            translations[lang] = (getattr(resp, "text", "") or "").strip() or f"Translation to {lang} failed"
        return translations
    except Exception as e:
        _raise_friendly_gemini_error(e)


# -------------------------
# Error Mapping
# -------------------------
def _raise_friendly_gemini_error(err: Exception):
    msg = str(err)
    if "500" in msg or "internal error" in msg.lower():
        raise Exception("AI service is temporarily unavailable. Please try again in a moment.")
    elif "429" in msg or "quota" in msg.lower():
        raise Exception("API quota exceeded. Please try again later.")
    elif "401" in msg or "403" in msg or "invalid" in msg.lower():
        raise Exception("API key is invalid or expired. Please check your configuration.")
    elif "CERTIFICATE_VERIFY_FAILED" in msg or "certificate" in msg.lower():
        raise Exception(
            "TLS certificate verification failed. If you are behind a proxy, ensure system CA certificates are installed, "
            "or run Python with certifi. In many setups, the official google SDK works out-of-the-box."
        )
    else:
        raise Exception(f"Failed to generate description: {msg}")

