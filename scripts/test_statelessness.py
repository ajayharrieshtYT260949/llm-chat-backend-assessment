
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.llm.service import get_openai_client


def main():
    client = get_openai_client()
    settings = get_settings()

    # First API request: tell the model a fact.
    first_response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "user",
                "content": "My favourite colour is blue. Remember this."
            }
        ],
        max_tokens=100,
    )

    print("First response:")
    print(first_response.choices[0].message.content)

    # Second API request: send only the new question.
    # The first request's messages are NOT included.
    stateless_response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "user",
                "content": "What is my favourite colour?"
            }
        ],
        max_tokens=100,
    )

    print("\nSecond response (without conversation history):")
    print(stateless_response.choices[0].message.content)

    # Third API request: include the previous conversation.
    stateful_response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "user",
                "content": "My favourite colour is blue. Remember this."
            },
            {
                "role": "assistant",
                "content": first_response.choices[0].message.content
            },
            {
                "role": "user",
                "content": "What is my favourite colour?"
            }
        ],
        max_tokens=100,
    )

    print("\nThird response (with conversation history):")
    print(stateful_response.choices[0].message.content)

    client.close()


if __name__ == "__main__":
    main()
