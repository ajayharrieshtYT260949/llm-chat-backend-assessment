
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.tools.executor import execute_tool, execute_tool_call
from app.tools.loop import run_tool_loop


# -----------------------------------------
# Tool execution error tests
# -----------------------------------------

def test_unknown_order_returns_error():
    result = execute_tool(
        "get_order_status",
        {"order_id": 9999}
    )

    assert result == {"error": "Order 9999 not found"}


def test_unknown_customer_returns_error():
    result = execute_tool(
        "get_customer",
        {"customer_id": 9999}
    )

    assert result == {"error": "Customer 9999 not found"}


def test_invalid_discount_returns_error():
    result = execute_tool(
        "calculate_discount",
        {
            "amount": 1000,
            "discount_percent": 150
        }
    )

    assert "error" in result


def test_unknown_tool_returns_error():
    result = execute_tool(
        "unknown_tool",
        {}
    )

    assert result == {"error": "Unknown tool: unknown_tool"}


def test_malformed_tool_arguments_return_error():
    tool_call = SimpleNamespace(
        id="call_invalid",
        function=SimpleNamespace(
            name="get_order_status",
            arguments="{invalid json"
        )
    )

    result = execute_tool_call(tool_call)

    assert result["tool_call_id"] == "call_invalid"
    assert "error" in result["result"]


# -----------------------------------------
# Parallel tool execution test
# -----------------------------------------

def test_three_tools_execute_in_one_round():

    tool_calls = [
        SimpleNamespace(
            id="call_order",
            function=SimpleNamespace(
                name="get_order_status",
                arguments='{"order_id": 1001}'
            )
        ),
        SimpleNamespace(
            id="call_customer",
            function=SimpleNamespace(
                name="get_customer",
                arguments='{"customer_id": 501}'
            )
        ),
        SimpleNamespace(
            id="call_discount",
            function=SimpleNamespace(
                name="calculate_discount",
                arguments='{"amount": 1000, "discount_percent": 20}'
            )
        ),
    ]

    assistant_message = MagicMock()
    assistant_message.tool_calls = tool_calls
    assistant_message.model_dump.return_value = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments
                }
            }
            for call in tool_calls
        ]
    }

    final_message = SimpleNamespace(
        content="All three tools completed successfully.",
        tool_calls=None
    )

    first_response = SimpleNamespace(
        choices=[
            SimpleNamespace(message=assistant_message)
        ]
    )

    second_response = SimpleNamespace(
        choices=[
            SimpleNamespace(message=final_message)
        ]
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            first_response,
            second_response
        ]
    )

    result = asyncio.run(
        run_tool_loop(
            messages=[
                {
                    "role": "user",
                    "content": "Check order, customer and discount."
                }
            ],
            client=mock_client
        )
    )

    assert result["tool_rounds"] == 1
    assert len(result["tool_results"]) == 3

    returned_ids = {
        item["tool_call_id"]
        for item in result["tool_results"]
    }

    assert returned_ids == {
        "call_order",
        "call_customer",
        "call_discount"
    }

    assert result["answer"] == (
        "All three tools completed successfully."
    )

    assert mock_client.chat.completions.create.await_count == 2
