
def calculate_cost(
    provider: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Calculate actual provider API charges.

    Local Ollama inference has no provider API charge.
    Hardware and electricity costs are not included.
    """

    if provider == "ollama":
        return 0.0

    raise ValueError(
        f"Unsupported provider for local execution: {provider}"
    )
