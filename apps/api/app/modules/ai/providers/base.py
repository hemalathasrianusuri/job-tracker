from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    model: str


class LLMProviderError(Exception):
    """Raised on any provider failure — the orchestrator catches this to trigger fallback."""


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, *, system: str, user: str, max_tokens: int) -> LLMResponse:
        raise NotImplementedError
