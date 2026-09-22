import asyncio
import os
import sys

import requests
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

SYSTEM = """You are a Terraform platform engineering assistant.
Use only approved modules exposed by MCP.
Never invent module names or required fields.
Ask for missing required values.
Validate before generating.
Never run terraform apply.
Always create a feature branch, never write to the base branch.
Prefer a draft Pull Request.
Explain the changes and provide the PR URL.
Respond in the user's language.
"""

def ollama_chat(messages, tools):
    r = requests.post(
        f"{os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')}/api/chat",
        json={
            "model": os.environ.get("OLLAMA_MODEL", "qwen3:8b"),
            "messages": messages,
            "tools": tools,
            "stream": False,
        },
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["message"]

async def main():
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "ai_terraform_mcp_lab.mcp_server.server"],
        env=os.environ.copy(),
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()
            tools = [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema or {"type": "object", "properties": {}},
                },
            } for tool in mcp_tools.tools]

            messages = [{"role": "system", "content": SYSTEM}]
            print("AI Terraform Agent listo. Escribe 'exit' para salir.")
            while True:
                user = input("\nTú: ").strip()
                if user.lower() in {"exit", "quit"}:
                    break
                messages.append({"role": "user", "content": user})
                for _ in range(12):
                    assistant = ollama_chat(messages, tools)
                    messages.append(assistant)
                    if not assistant.get("tool_calls"):
                        print(f"\nAgente: {assistant.get('content', '')}")
                        break
                    for call in assistant["tool_calls"]:
                        result = await session.call_tool(
                            call["function"]["name"],
                            call["function"].get("arguments", {}),
                        )
                        content = "".join(block.text for block in result.content if hasattr(block, "text"))
                        messages.append({"role": "tool", "content": content})
                else:
                    print("\nAgente: alcanzó el límite de pasos de esta solicitud.")

if __name__ == "__main__":
    asyncio.run(main())
