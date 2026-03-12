import os
import json
from groq import Groq

class FakeBlock:
    def __init__(self, type_, text=None, id=None, name=None, input=None):
        self.type = type_
        self.text = text
        self.id = id
        self.name = name
        self.input = input

class FakeMessage:
    def __init__(self, content, stop_reason="end_turn"):
        self.content = content
        self.stop_reason = stop_reason

class Claude:
    def __init__(self, model: str):
        self.model = "llama-3.3-70b-versatile"
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def add_user_message(self, messages: list, message):
        text = message.content[0].text if isinstance(message, FakeMessage) and message.content and message.content[0].type == "text" else message
        if isinstance(text, dict): text = text.get("content", "")
        messages.append({"role": "user", "content": str(text)})

    def add_assistant_message(self, messages: list, message):
        msg_dict = {"role": "assistant", "content": ""}
        if isinstance(message, FakeMessage):
            # Extract text if it exists
            text = "\n".join([b.text for b in message.content if b.type == "text" and b.text])
            if text:
                msg_dict["content"] = text
            
            # CRITICAL FIX: Extract tool calls and save them in the message history for Groq
            tool_calls = []
            for b in message.content:
                if b.type == "tool_use":
                    tool_calls.append({
                        "id": b.id,
                        "type": "function",
                        "function": {"name": b.name, "arguments": json.dumps(b.input)}
                    })
            if tool_calls:
                msg_dict["tool_calls"] = tool_calls
        else:
            msg_dict["content"] = str(message)
            
        messages.append(msg_dict)

    def add_tool_message(self, messages: list, tool_result_parts: list):
        # CRITICAL FIX: Translates the MCP output into Groq's required tool response format
        for part in tool_result_parts:
            messages.append({
                "role": "tool",
                "tool_call_id": part["tool_use_id"],
                "content": str(part["content"])
            })

    def text_from_message(self, message):
        if isinstance(message, FakeMessage):
            return "\n".join([block.text for block in message.content if block.type == "text" and block.text])
        return str(message)

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=[],
        tools=None,
        thinking=False,
        thinking_budget=1024,
    ):
        params = {
            "model": self.model,
            "messages": [],
            "temperature": temperature,
        }

        if system:
            params["messages"].append({"role": "system", "content": system})
            
        for m in messages:
            if isinstance(m["content"], list):
                text_content = " ".join([b.get("text", "") for b in m["content"] if isinstance(b, dict) and b.get("type") == "text"])
                params["messages"].append({"role": m["role"], "content": text_content})
            else:
                params["messages"].append(m)

        if tools:
            groq_tools = []
            for t in tools:
                groq_tools.append({
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t["input_schema"]
                    }
                })
            params["tools"] = groq_tools
            params["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**params)
        
        response_message = response.choices[0].message
        blocks = []
        stop_reason = "end_turn"
        
        if response_message.content:
            blocks.append(FakeBlock(type_="text", text=response_message.content))
            
        if response_message.tool_calls:
            stop_reason = "tool_use"
            for tool_call in response_message.tool_calls:
                blocks.append(FakeBlock(
                    type_="tool_use",
                    id=tool_call.id,
                    name=tool_call.function.name,
                    input=json.loads(tool_call.function.arguments)
                ))
                
        return FakeMessage(content=blocks, stop_reason=stop_reason)