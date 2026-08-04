"""Test-only fakes for external dependencies. Let tests script exact
responses (or exceptions) without any network access or API key."""


class FakeLLMClient:
    def __init__(self, responses: list) -> None:
        self._responses = iter(responses)
        self.prompts_seen: list = []

    def generate(self, prompt: str) -> str:
        self.prompts_seen.append(prompt)
        item = next(self._responses)
        if isinstance(item, Exception):
            raise item
        return item


class FakeHttpResponse:
    def __init__(self, status_code: int = 200, json_data=None, raise_on_json: bool = False) -> None:
        self.status_code = status_code
        self._json_data = json_data
        self._raise_on_json = raise_on_json

    def json(self):
        if self._raise_on_json:
            raise ValueError("invalid JSON body")
        return self._json_data


class FakeHttpGet:
    def __init__(self, responses: list) -> None:
        self._responses = iter(responses)
        self.calls_seen: list = []

    def __call__(self, url, *, params=None, timeout=None, headers=None):
        self.calls_seen.append({"url": url, "params": params, "timeout": timeout, "headers": headers})
        item = next(self._responses)
        if isinstance(item, Exception):
            raise item
        return item