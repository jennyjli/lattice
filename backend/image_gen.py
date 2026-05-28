"""
Image generation module.

Generates educational diagrams using Google Gemini (Nano Banana) or OpenAI image generation.
Includes adaptive fallback logic when direct image generation is unavailable.
"""

import base64
from typing import Optional
from google import genai
from google.genai import types
from openai import OpenAI
from config import (
    GEMINI_API_KEY,
    GEMINI_IMAGE_MODEL,
    OPENAI_API_KEY,
    IMAGE_GEN_PROVIDER,
    IMAGE_SIZE,
)


class ImageGenerator:
    """
    Generates educational scientific visualizations using AI image generation.

    Supports:
    - Google Gemini Nano Banana (gemini-2.5-flash-image) native image generation
    - OpenAI image generation fallback
    - Graceful fallback when neither provider can produce an image
    """

    def __init__(self):
        self.provider = IMAGE_GEN_PROVIDER.lower()
        self.gemini_available = False
        self.gemini_client = None
        self.openai_available = bool(OPENAI_API_KEY)
        self.openai_client = None

        if self.provider == "openai":
            if self.openai_available:
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
                print("✅ OpenAI image generation initialized")
            else:
                print("⚠️  OpenAI image provider selected but OPENAI_API_KEY is missing. Image generation unavailable.")

        if self.provider == "gemini":
            if GEMINI_API_KEY:
                try:
                    self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                    self.gemini_available = True
                    print(f"✅ Gemini (Nano Banana) image generation initialized using model {GEMINI_IMAGE_MODEL}")
                except Exception as e:
                    print(f"⚠️  Gemini initialization failed: {e}")
            else:
                print("⚠️  Gemini image provider selected but GEMINI_API_KEY is missing. Image generation unavailable.")

    def generate_image(
        self,
        concept: str,
        concept_type: str,
        domain: str,
        mechanisms: list[str],
        style: str,
    ) -> Optional[str]:
        """
        Generate an image for a scientific concept.

        Returns base64-encoded PNG data URI when successful.
        """
        prompt = self._build_prompt(concept, concept_type, domain, mechanisms, style)

        if self.provider == "gemini" and self.gemini_available:
            return self._generate_gemini_image(prompt)

        if self.provider == "openai" and self.openai_available:
            return self._generate_openai_image(prompt)

        return None

    def _build_prompt(
        self,
        concept: str,
        concept_type: str,
        domain: str,
        mechanisms: list[str],
        style: str,
    ) -> str:
        mechanisms_text = "\n".join([f"  - {m}" for m in mechanisms[:4]])
        return f"""Create a publication-quality scientific illustration for the following concept.

Concept: {concept}
Concept Type: {concept_type}
Domain: {domain}
Style: {style}

Key Mechanisms/Steps:
{mechanisms_text}

Instructions:
- Render a clear scientific diagram with labels and arrows.
- Emphasize the important mechanisms in a step-by-step layout.
- Keep the visualization accessible for learners.
- Use a modern, clean visual style.
- Prefer a compact, illustration-style composition.
"""

    def _generate_gemini_image(self, prompt: str) -> Optional[str]:
        """
        Generate an image using Gemini Nano Banana (gemini-2.5-flash-image).

        Nano Banana returns images as inline_data parts in generate_content responses.
        """
        try:
            response = self.gemini_client.models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["image"],
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/png"
                    b64 = base64.b64encode(image_bytes).decode()
                    return f"data:{mime_type};base64,{b64}"
            print("Gemini returned no image parts in response.")
            return None
        except Exception as e:
            print(f"Gemini image generation failed: {e}")
            return None

    def _generate_openai_image(self, prompt: str) -> Optional[str]:
        try:
            response = self.openai_client.images.generate(
                prompt=prompt,
                size=IMAGE_SIZE,
                response_format="b64_json",
            )
            image_b64 = response.data[0].b64_json
            if image_b64:
                return f"data:image/png;base64,{image_b64}"
        except Exception as e:
            print(f"OpenAI image generation failed: {e}")
        return None

    def generate_html_embed(self, image_base64: str) -> str:
        return f'<img src="{image_base64}" style="max-width: 100%; border-radius: 8px;" />'


class ImageGenerationFallback:
    @staticmethod
    def generate_description_card(
        concept: str,
        domain: str,
        mechanisms: list[str],
        annotations: list,
    ) -> str:
        mechanisms_html = "".join([f"<li>{m}</li>" for m in mechanisms[:5]])
        annotations_html = "".join(
            [
                f'<div class="annotation"><strong>{a.label}:</strong> {a.description or ""}</div>'
                for a in annotations[:4]
            ]
        )
        html = f"""
        <div class="visualization-fallback" style="
            border-left: 4px solid #0ea5e9;
            padding: 16px;
            background-color: #f0f9ff;
            border-radius: 8px;
            margin: 16px 0;
        ">
            <h3 style="color: #0369a1; margin-top: 0;">
                {concept} - {domain.title()} Concept
            </h3>

            <div style="margin: 12px 0;">
                <h4 style="color: #075985; font-size: 14px;">Key Mechanisms:</h4>
                <ul style="margin: 8px 0; padding-left: 20px;">
                    {mechanisms_html}
                </ul>
            </div>

            <div style="margin: 12px 0;">
                <h4 style="color: #075985; font-size: 14px;">Components:</h4>
                {annotations_html}
            </div>

            <p style="color: #0284c7; font-size: 12px; margin-bottom: 0;">
                ℹ️ Enhanced visualization coming soon. Enable image generation for detailed diagrams.
            </p>
        </div>
        """
        return html


# Global instance
image_gen = ImageGenerator()
fallback_gen = ImageGenerationFallback()
