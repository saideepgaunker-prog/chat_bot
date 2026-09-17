import asyncio
from typing import AsyncGenerator, Dict, Any, List
from app.llm.base import BaseLLMClient
from app.core.config import settings
from app.core.logger import logger

class GeminiClient(BaseLLMClient):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.DEFAULT_MODEL_NAME
        self._configured = False
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._configured = True
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str = "",
        context_data: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not self._configured:
            yield {"type": "error", "message": "Gemini API key not configured"}
            return

        try:
            import google.generativeai as genai
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction if system_instruction else None
            )
            response = await asyncio.to_thread(model.generate_content, prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield {"type": "token", "delta": chunk.text}
                    await asyncio.sleep(0.01)
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield {"type": "error", "message": str(e)}
