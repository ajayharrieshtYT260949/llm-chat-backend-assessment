
import asyncio
import json

from openai import AsyncOpenAI

from app.config import get_settings
from app.llm.async_service import get_async_openai_client
from app.tools.executor import execute_tool_call
from app.tools.schemas import TOOLS


MAX_TOOL_ROUNDS = 5


async def execute_tool_calls(tool_calls: list) -> list[dict]:
    """
    Execute all tool calls in one round concurrently.

    Each result retains its original tool_call_id.
    """

    results = await asyncio.gather(
        *(
            asyncio.to_thread(execute_tool_call, tool_call)
            for tool_call in tool_calls
        )
    )

    return results


async def run_tool_loop(
    messages: list[dict],
    client: AsyncOpenAI | None = None,
    max_rounds: int = MAX_TOOL_ROUNDS,
) -> dict:
    """
    Run the LLM tool-calling cycle until a final answer
    is produced or the maximum number of rounds is reached.
    """

    if max_rounds < 1:
        raise ValueError("max_rounds must be at least 1")

    settings = get_settings()

    conversation = [message.copy() for message in messages]

    owned_client = client is None

    if owned_client:
        client = get_async_openai_client()

    tool_rounds = 0
    all_tool_results = []

    try:
        while tool_rounds < max_rounds:

            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=conversation,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=settings.max_output_tokens,
            )

            assistant_message = response.choices[0].message

            # No tool calls means the model has completed its answer.
            if not assistant_message.tool_calls:

                return {
                    "answer": assistant_message.content or "",
                    "tool_rounds": tool_rounds,
                    "tool_results": all_tool_results,
                    "messages": conversation,
                }

            # Preserve the assistant's tool-call request in history.
            conversation.append(
                assistant_message.model_dump(
                    exclude_none=True
                )
            )

            tool_rounds += 1

            # Execute every tool call in this round concurrently.
            results = await execute_tool_calls(
                assistant_message.tool_calls
            )

            all_tool_results.extend(results)

            # Send each result back using its matching tool_call_id.
            for result in results:

                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "content": json.dumps(result["result"]),
                    }
                )

        return {
            "answer": "",
            "tool_rounds": tool_rounds,
            "tool_results": all_tool_results,
            "messages": conversation,
            "error": (
                f"Maximum tool rounds ({max_rounds}) reached."
            ),
        }

    finally:
        if owned_client:
            await client.close()
