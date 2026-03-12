from core.claude import Claude
from mcp_client import MCPClient
from core.tools import ToolManager
from anthropic.types import MessageParam

class Chat:
    def __init__(self, claude_service: Claude, clients: dict[str, MCPClient]):
        self.claude_service: Claude = claude_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[MessageParam] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(
        self,
        query: str,
    ) -> str:
        final_text_response = ""

        await self._process_query(query)

        while True:
            # 1. Fetch the tools and print them so we KNOW the server isn't dead
            tools_list = await ToolManager.get_all_tools(self.clients)
            print(f"[SYSTEM DEBUG] Available Tools: {[t['name'] for t in tools_list]}")

            # 2. Force Groq to use the tool via a lethal System Prompt
            response = self.claude_service.chat(
                messages=self.messages,
                tools=tools_list,
                system="You are an autonomous AI agent with access to the local file system. DO NOT guess the contents of files. If the user asks about a file, YOU MUST use the read_local_file tool to read it immediately."
            )

            self.claude_service.add_assistant_message(self.messages, response)

            if response.stop_reason == "tool_use":
                print(self.claude_service.text_from_message(response))
                tool_result_parts = await ToolManager.execute_tool_requests(
                    self.clients, response
                )

                # CRITICAL FIX: Push the tool result to Groq securely using the proper sequence
                self.claude_service.add_tool_message(
                    self.messages, tool_result_parts
                )
            else:
                final_text_response = self.claude_service.text_from_message(
                    response
                )
                break

        return final_text_response