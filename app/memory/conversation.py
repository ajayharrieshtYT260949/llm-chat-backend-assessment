
from openai import AsyncOpenAI

from app.config import get_settings
from app.llm.async_service import get_async_openai_client
from app.llm.token_counter import count_tokens
from app.tools.loop import run_tool_loop


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI assistant. "
    "Answer questions clearly and accurately. "
    "Use available tools when necessary."
)

SYSTEM_TOKEN_LIMIT = 500
HISTORY_TOKEN_LIMIT = 3000
OUTPUT_TOKEN_LIMIT = 1000


class Conversation:

    def __init__(
        self,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT
    ):
        if count_tokens([
            {"role": "system", "content": system_prompt}
        ]) > SYSTEM_TOKEN_LIMIT:
            raise ValueError("System prompt exceeds 500 tokens.")

        self.system_prompt = system_prompt

        self.messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        self.summary = ""

        # Preserve the first conversation exchange during summarization.
        self.pinned_messages = []

    def add_user_message(self, content: str) -> None:
        self.messages.append({
            "role": "user",
            "content": content
        })

    def add_assistant_message(self, content: str) -> None:
        self.messages.append({
            "role": "assistant",
            "content": content
        })

    def get_messages(self) -> list[dict]:
        return [message.copy() for message in self.messages]

    def get_history_messages(self) -> list[dict]:
        return [
            message.copy()
            for message in self.messages
            if message["role"] != "system"
        ]

    def get_token_count(self) -> int:
        return count_tokens(self.get_messages())



    async def summarize_messages(
        self,
        messages: list[dict],
        client: AsyncOpenAI | None = None
    ) -> str:
        """
        Summarize older messages in smaller chronological chunks.
        Carry important facts forward between chunks.
        """

        owned_client = client is None

        if owned_client:
            client = get_async_openai_client()

        try:
            running_summary = self.summary

            # Process older messages chronologically.
            chunk_size = 8

            for start in range(0, len(messages), chunk_size):
                chunk = messages[start:start + chunk_size]

                conversation_text = "\n".join(
                    f"{message['role'].upper()}: "
                    f"{message.get('content', '')}"
                    for message in chunk
                )

                response = await client.chat.completions.create(
                    model=get_settings().openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a persistent conversation "
                                "memory manager.\n"
                                "Your job is to merge new conversation "
                                "records into an existing memory.\n\n"
                                "IMPORTANT RULES:\n"
                                "1. Preserve the user's name.\n"
                                "2. Preserve personal preferences.\n"
                                "3. Preserve important facts and decisions.\n"
                                "4. Never discard an existing fact unless "
                                "the user explicitly corrects it.\n"
                                "5. Remove repetitive details.\n"
                                "6. Never invent information.\n"
                                "7. Return only the updated factual memory."
                            )
                        },
                        {
                            "role": "user",
                            "content": (
                                "EXISTING MEMORY:\n"
                                f"{running_summary or 'No existing memory.'}"
                                "\n\nNEW CONVERSATION RECORDS:\n"
                                f"{conversation_text}"
                                "\n\nMerge these into one concise memory. "
                                "Keep all important existing facts."
                            )
                        }
                    ],
                    max_tokens=400
                )

                chunk_summary = (
                    response.choices[0].message.content or ""
                ).strip()

                if chunk_summary:
                    running_summary = chunk_summary

            return running_summary

        finally:
            if owned_client:
                await client.close()



    async def manage_history(
        self,
        client: AsyncOpenAI | None = None
    ) -> None:
        """
        Preserve the first conversation exchange,
        summarize older messages, and retain recent messages.
        """

        history = self.get_history_messages()

        if count_tokens(history) <= HISTORY_TOKEN_LIMIT:
            return

        # Preserve the first user/assistant exchange.
        if not self.pinned_messages:
            self.pinned_messages = [
                message.copy()
                for message in history[:2]
            ]

        pinned_count = len(self.pinned_messages)

        # Exclude protected messages from summarization.
        remaining_history = history[pinned_count:]

        # Keep approximately 40% of the history budget
        # for the most recent messages.
        recent_limit = int(HISTORY_TOKEN_LIMIT * 0.4)

        recent_messages = []
        recent_tokens = 0

        for message in reversed(remaining_history):
            message_tokens = count_tokens([message])

            if recent_tokens + message_tokens > recent_limit:
                break

            recent_messages.insert(0, message)
            recent_tokens += message_tokens

        # Everything between protected and recent messages
        # becomes the summarization input.
        recent_count = len(recent_messages)

        older_messages = (
            remaining_history[:-recent_count]
            if recent_count
            else remaining_history
        )

        if not older_messages:
            return

        new_summary = await self.summarize_messages(
            older_messages,
            client=client
        )

        # Include protected original messages in the summary
        # as exact text, not as LLM-generated paraphrases.
        protected_context = "\n".join(
            f"{message['role'].upper()}: {message.get('content', '')}"
            for message in self.pinned_messages
        )

        self.summary = (
            "PROTECTED EARLY CONVERSATION:\n"
            + protected_context
            + "\n\nSUMMARY OF OLDER CONVERSATION:\n"
            + new_summary
        )

        summary_message = {
            "role": "system",
            "content": (
                "Conversation memory. Preserve these facts:\n"
                + self.summary
            )
        }

        # Rebuild the conversation without losing protected messages.
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            summary_message,
            *self.pinned_messages,
            *recent_messages
        ]

        # Keep the conversation history within its budget.
        while (
            count_tokens(self.get_history_messages())
            > HISTORY_TOKEN_LIMIT
            and len(recent_messages) > 1
        ):
            recent_messages.pop(0)

            self.messages = [
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                summary_message,
                *self.pinned_messages,
                *recent_messages
            ]

    async def send(
        self,
        content: str,
        client: AsyncOpenAI | None = None
    ) -> dict:

        self.add_user_message(content)

        await self.manage_history(client=client)

        result = await run_tool_loop(
            messages=self.get_messages(),
            client=client
        )

        self.messages = result["messages"]

        if result.get("answer"):
            self.add_assistant_message(result["answer"])

        return result
