"""Provider selection for the fixed-evidence benchmark runner."""

from .gemini import GeminiClient
from .soclaas import SoCLaaSClient


def create_client(provider, timeout, max_retries, insecure_tls=False):
    if provider == "gemini":
        return GeminiClient(timeout=timeout, max_retries=max_retries,
                            insecure_tls=insecure_tls)
    if provider == "soclaas":
        client = SoCLaaSClient(timeout=timeout, max_retries=max_retries,
                               insecure_tls=insecure_tls)
        client.provider = "soclaas"
        return client
    raise ValueError(f"Unknown provider: {provider!r}")
