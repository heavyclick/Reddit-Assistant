import google.generativeai as genai
from typing import Optional
from config.settings import settings


class LLMClient:
    """Unified LLM client supporting Gemini and OpenAI"""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

        if self.provider == "gemini":
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == "openai":
            # Only import OpenAI if needed
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text using configured LLM"""
        temp = temperature or self.temperature
        max_tok = max_tokens or self.max_tokens

        if self.provider == "gemini":
            return await self._generate_gemini(system_prompt, user_prompt, temp, max_tok)
        elif self.provider == "openai":
            return await self._generate_openai(system_prompt, user_prompt, temp, max_tok)

    async def _generate_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using Google Gemini"""
        try:
            # Combine system and user prompts for Gemini
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            response = self.client.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            )

            return response.text

        except Exception as e:
            print(f"Gemini generation error: {e}")
            raise

    async def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"OpenAI generation error: {e}")
            raise


# Lazy-load global instance
_llm_client_instance = None

def get_llm_client() -> LLMClient:
    """Get LLMClient instance (lazy-loaded)"""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance
