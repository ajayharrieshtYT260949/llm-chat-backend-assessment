
import json


# Sample order records for demonstration.
ORDERS = {
    1001: {
        "order_id": 1001,
        "customer_id": 501,
        "status": "Shipped",
        "estimated_delivery": "2026-11-25",
    },
    1002: {
        "order_id": 1002,
        "customer_id": 502,
        "status": "Processing",
        "estimated_delivery": "2026-11-28",
    },
    1003: {
        "order_id": 1003,
        "customer_id": 501,
        "status": "Delivered",
        "estimated_delivery": "2026-11-18",
    },
}


# Sample customer records for demonstration.
CUSTOMERS = {
    501: {
        "customer_id": 501,
        "name": "Alex Johnson",
        "email": "alex@example.com",
        "membership": "Gold",
    },
    502: {
        "customer_id": 502,
        "name": "Sarah Williams",
        "email": "sarah@example.com",
        "membership": "Silver",
    },
}


def get_order_status(order_id: int) -> dict:
    """Retrieve order details using an order ID."""

    if isinstance(order_id, bool) or not isinstance(order_id, int):
        raise ValueError("order_id must be an integer")

    order = ORDERS.get(order_id)

    if order is None:
        raise ValueError(f"Order {order_id} not found")

    return order.copy()


def get_customer(customer_id: int) -> dict:
    """Retrieve customer details using a customer ID."""

    if isinstance(customer_id, bool) or not isinstance(customer_id, int):
        raise ValueError("customer_id must be an integer")

    customer = CUSTOMERS.get(customer_id)

    if customer is None:
        raise ValueError(f"Customer {customer_id} not found")

    return customer.copy()


def calculate_discount(
    amount: float,
    discount_percent: float,
) -> dict:
    """Calculate discount amount and final purchase price."""

    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("amount must be a number")

    if isinstance(discount_percent, bool) or not isinstance(
        discount_percent, (int, float)
    ):
        raise ValueError("discount_percent must be a number")

    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    if not 0 <= discount_percent <= 100:
        raise ValueError("discount_percent must be between 0 and 100")

    discount_amount = amount * discount_percent / 100
    final_price = amount - discount_amount

    return {
        "original_amount": round(amount, 2),
        "discount_percent": discount_percent,
        "discount_amount": round(discount_amount, 2),
        "final_price": round(final_price, 2),
    }


# Maps tool names to their Python implementations.
TOOL_FUNCTIONS = {
    "get_order_status": get_order_status,
    "get_customer": get_customer,
    "calculate_discount": calculate_discount,
}


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a requested tool and return a structured result."""

    try:
        function = TOOL_FUNCTIONS.get(tool_name)

        if function is None:
            return {
                "error": f"Unknown tool: {tool_name}"
            }

        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a JSON object")

        result = function(**arguments)

        return result

    except (TypeError, ValueError) as error:
        return {
            "error": str(error)
        }


def execute_tool_call(tool_call) -> dict:
    """Execute one OpenAI-compatible tool call."""

    tool_call_id = tool_call.id
    tool_name = tool_call.function.name

    try:
        arguments = json.loads(tool_call.function.arguments)

        result = execute_tool(
            tool_name=tool_name,
            arguments=arguments,
        )

    except (json.JSONDecodeError, TypeError, ValueError) as error:
        result = {
            "error": f"Invalid tool arguments: {error}"
        }

    return {
        "tool_call_id": tool_call_id,
        "name": tool_name,
        "result": result,
    }
