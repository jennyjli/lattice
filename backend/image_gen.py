"""
Image generation module.

Generates educational diagrams using Google Gemini or OpenAI image generation.
Includes adaptive fallback logic when direct image generation is unavailable.
"""

import base64
from typing import Optional
import google.generativeai as genai
from openai import OpenAI
from config import (
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    IMAGE_GEN_PROVIDER,
    IMAGE_SIZE,
)


class ImageGenerator:
    """
    Generates educational scientific visualizations using AI image generation.

    Supports:
    - Google Gemini prompt refinement and image intent
    - OpenAI image generation fallback
    - Graceful fallback when neither provider can produce an image
    """

    def __init__(self):
        self.provider = IMAGE_GEN_PROVIDER.lower()
        self.gemini_available = False
        self.openai_available = bool(OPENAI_API_KEY)
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if self.openai_available else None

        if self.provider == "gemini" and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.generative_models.GenerativeModel("gemini-pro-vision")
                self.gemini_available = True
                print("✅ Gemini prompt generation initialized")
            except Exception as e:
                print(f"⚠️  Gemini initialization failed: {e}")
                self.gemini_available = False

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

        Returns base64-encoded PNG data when successful.
        """
        prompt = self._build_prompt(concept, concept_type, domain, mechanisms, style)

        if self.provider == "gemini" and self.gemini_available:
            image_data = self._try_gemini_image(prompt)
            if image_data:
                return self._encode_image(image_data)

            if self.openai_available:
                refined_prompt = self._refine_prompt_with_gemini(prompt) or prompt
                return self._generate_openai_image(refined_prompt)

            return None

        if self.provider == "openai" and self.openai_available:
            return self._generate_openai_image(prompt)

        if self.openai_available:
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
        prompt = f"""Create a publication-quality scientific illustration for the following concept.

Concept: {concept}
Concept Type: {concept_type}
Domain: {domain}
Style: {style}

Key Mechanisms/Steps:
{mechanisms_text}

Instructions:
- Render a clear scientific diagram with labels and arrows.
- Emphasize the important mechanisms in a step-by-step layout.
- Keep the solution accessible for learners.
- Use a modern, clean visual style.
- Prefer a compact, illustration-style composition.

Return a prompt suitable for image generation or a direct image asset if supported.
"""
        return prompt

    def _try_gemini_image(self, prompt: str) -> Optional[bytes]:
        try:
            if not self.gemini_available:
                return None

            response = self.gemini_model.generate_content(contents=[prompt])
            if hasattr(response, 'to_dict'):
                response_dict = response.to_dict()
                print('Gemini response metadata:', response_dict.get('metadata', {}))

            # Attempt to extract a PNG image from Gemini content if available.
            if hasattr(response, 'content') and response.content:
                content = response.content
                if isinstance(content, bytes):
                    return content
                if isinstance(content, str):
                    print('Gemini returned text content for image request.')
                    return None

            return None
        except Exception as error:
            print(f"Gemini image generation failed: {error}")
            return None

    def _refine_prompt_with_gemini(self, prompt: str) -> str:
        try:
            if not self.gemini_available:
                return prompt

            rewrite_prompt = (
                "Rewrite the following prompt for the best possible scientific diagram generation. "
                "Keep instructions concise, visual, and clear for a model that can render diagrams.\n\n"
                f"{prompt}"
            )
            result = genai.generate_text(model="gemini-pro", prompt=rewrite_prompt)
            if result and getattr(result, 'text', None):
                return result.text.strip()
        except Exception as error:
            print(f"Gemini prompt refinement failed: {error}")

        return prompt

    def _generate_openai_image(self, prompt: str) -> Optional[str]:
        try:
            if not self.openai_client:
                return None

            response = self.openai_client.images.generate(
                prompt=prompt,
                size=IMAGE_SIZE,
                response_format="b64_json",
            )
            image_b64 = response.data[0].b64_json
            if image_b64:
                return f"data:image/png;base64,{image_b64}"
        except Exception as error:
            print(f"OpenAI image generation failed: {error}")

        return None

    def _encode_image(self, image_data: bytes) -> str:
        return f"data:image/png;base64,{base64.b64encode(image_data).decode()}"

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
