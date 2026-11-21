import asyncio
import json
import sys
from pathlib import Path

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.tools.loop import run_tool_loop


async def main():

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful customer support assistant. "
                "Use the available tools whenever necessary. "
                "After receiving tool results, explain them clearly."
            ),
        },
        {
            "role": "user",
            "content": (
                "Please do three things: "
                "check order 1001, "
                "get customer 501 details, "
                "and calculate a 20 percent discount on 1000."
            ),
        },
    ]

    result = await run_tool_loop(messages)

    print("\n========== TOOL LOOP RESULT ==========")

    print("Tool rounds:", result["tool_rounds"])

    print("\nTool results:")

    for item in result["tool_results"]:
        print(
            json.dumps(
                item,
                indent=4
            )
        )

    print("\nFinal answer:")
    print(result["answer"])

    if "error" in result:
        print("\nLoop error:", result["error"])

    print("\n======================================")


if __name__ == "__main__":
    asyncio.run(main())
