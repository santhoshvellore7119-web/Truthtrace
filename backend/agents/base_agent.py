from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class AgentResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BaseAgent(ABC):
    """Base class for all agents in the TruthTrace pipeline."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """Execute the agent's logic."""
        pass

    def log(self, message: str):
        """Simple logging (can be replaced with proper logger)."""
        print(f"[{self.name}] {message}")