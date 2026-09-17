from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List

class BaseLLMClient(ABC):
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str = "",
        context_data: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        pass
