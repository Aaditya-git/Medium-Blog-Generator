import os
from typing import Optional, Dict, Any, List

class ClaudeClient:
    """Very small wrapper.
    If ANTHROPIC_API_KEY is absent, returns None so stages use fallback data."""
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')

    def available(self) -> bool:
        return bool(self.api_key)

    def research(self, topic: str) -> Dict[str, Any]:
        # NOTE: keep it simple — real call removed to avoid dependency issues.
        # If API available, you could integrate Anthropic SDK here.
        # For now we return None to force fallback in research_stage when not configured.
        return None
