import requests

from langchain.llms import BaseLLM
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs.llm_result import LLMResult
from typing import List, Optional, Any


class PerplexityAILLM(BaseLLM):
    api_key: str
    model_name: str

    def call_perplexity_ai(self, prompt: str) -> LLMResult:
        url = "https://api.perplexity.ai/chat/completions"

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "Be precise and concise."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json",
            "content-type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        # Convert the response JSON to dictionary
        json_response = response.json()

        return json_response

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None,
                  run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> LLMResult:
        generations = []
        for prompt in prompts:
            generations.append([self._call(prompt, stop=stop, **kwargs)])
        return LLMResult.construct(generations=generations)

    def _call(self, prompt: str, stop: Optional[List[str]] = None, max_tokens: Optional[int] = None) -> LLMResult:
        response_data = self.call_perplexity_ai(prompt)
        model = LLMResult.construct(text=response_data['choices'][0]["message"]["content"])

        return model

    @property
    def _llm_type(self) -> str:
        return "PerplexityAI"
