
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.memory.conversation import Conversation


async def main():

    conversation = Conversation()

    questions = [
        "My name is Alex and I am learning Python.",
        "What is my name?",
        "Which programming language am I learning?",
        "Can you summarize what you know about me?"
    ]

    for turn, question in enumerate(questions, start=1):

        print(f"\n========== TURN {turn} ==========")
        print("User:", question)

        result = await conversation.send(question)

        print("Assistant:", result["answer"])
        print("Messages stored:", len(conversation.messages))

    print("\n========== FINAL CONVERSATION HISTORY ==========")

    for message in conversation.get_messages():
        print(f"\nRole: {message['role']}")
        print("Content:", message.get("content", ""))


if __name__ == "__main__":
    asyncio.run(main())
