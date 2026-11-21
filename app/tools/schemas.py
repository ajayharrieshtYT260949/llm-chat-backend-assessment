
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": (
                "Retrieve the current status and delivery information "
                "for a customer order using its order ID. "
                "Use this when a customer asks where their order is "
                "or wants to know its delivery status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "integer",
                        "description": "The unique numeric ID of the order.",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": (
                "Retrieve customer information using a customer ID, "
                "including their name, email, and membership tier. "
                "Use this when customer details are requested."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "The unique numeric ID of the customer.",
                    }
                },
                "required": ["customer_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_discount",
            "description": (
                "Calculate the discount amount and final payable price "
                "for a purchase. Use this when a customer asks about "
                "a discount or the final price after a discount."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The original purchase amount. Must be positive.",
                    },
                    "discount_percent": {
                        "type": "number",
                        "description": "Discount percentage, from 0 to 100.",
                    },
                },
                "required": ["amount", "discount_percent"],
                "additionalProperties": False,
            },
        },
    },
]
