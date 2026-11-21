
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory.conversation import Conversation
from app.llm.token_counter import count_tokens


async def main():

    conversation = Conversation()

    # Add an important early fact.
    conversation.add_user_message(
        "My name is Alex. My favourite programming language is Python."
    )

    conversation.add_assistant_message(
        "Nice to meet you, Alex! Python is a great language."
    )

    print("Important early fact added.")

    # Add enough messages to exceed the history budget.
    for turn in range(1, 31):

        conversation.add_user_message(
            f"Turn {turn}: Explain Python programming concept number "
            f"{turn}. Include examples, advantages and disadvantages. "
            * 15
        )

        conversation.add_assistant_message(
            f"Turn {turn}: Python concept explanation. "
            "This explanation includes detailed information, "
            "examples, implementation details and practical usage. "
            * 15
        )

    before = count_tokens(conversation.get_history_messages())

    print("\n========== BEFORE SUMMARIZATION ==========")
    print("History tokens:", before)
    print("Message count:", len(conversation.messages))

    # Use the real LLM to summarize older messages.
    # Inspect original conversation history before summarization.
    history = conversation.get_history_messages()

    print("\n========== FIRST 4 MESSAGES ==========")

    for message in history[:4]:
        print(message["role"], ":", message["content"][:200])

    print("\n========== LAST 4 MESSAGES ==========")

    for message in history[-4:]:
        print(message["role"], ":", message["content"][:200])

    # Use the real LLM to summarize older messages.
    await conversation.manage_history()

    after = count_tokens(conversation.get_history_messages())

    print("\n========== AFTER SUMMARIZATION ==========")
    print("History tokens:", after)
    print("Message count:", len(conversation.messages))

    print("\nSummary:")
    print(conversation.summary)

    print("\n========== VALIDATION ==========")

    print(
        "History within budget:",
        after <= 3000
    )

    print(
        "Original system prompt preserved:",
        conversation.messages[0]["content"]
        == conversation.system_prompt
    )

    print(
        "Summary created:",
        bool(conversation.summary)
    )

    print(
        "Recent messages retained:",
        len(conversation.messages) > 2
    )

    print("\n================================")


if __name__ == "__main__":
    asyncio.run(main())
