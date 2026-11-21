
from openai import OpenAI
from anthropic import Anthropic

MODEL = "qwen2.5:1.5b"

# Test 1: OpenAI official Python SDK
openai_client = OpenAI(
    base_url="http://localhost:11434/v1/",
    api_key="ollama",
)

print("\n========== OPENAI SDK TEST ==========")

openai_response = openai_client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": "Explain REST APIs in two sentences."
        }
    ],
)

print("Provider interface: OpenAI SDK")
print("Model:", openai_response.model)
print("Answer:", openai_response.choices[0].message.content)
print("Usage:", openai_response.usage)


# Test 2: Anthropic official Python SDK
anthropic_client = Anthropic(
    base_url="http://localhost:11434",
    api_key="ollama",
)

print("\n========== ANTHROPIC SDK TEST ==========")

anthropic_response = anthropic_client.messages.create(
    model=MODEL,
    max_tokens=150,
    system="You are a helpful technical assistant.",
    messages=[
        {
            "role": "user",
            "content": "Explain REST APIs in two sentences."
        }
    ],
)

print("Provider interface: Anthropic SDK")
print("Model:", anthropic_response.model)
print("Answer:", anthropic_response.content[0].text)
print("Usage:", anthropic_response.usage)

print("\nBoth SDK connection tests completed.")
