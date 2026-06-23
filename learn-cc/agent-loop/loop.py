import os
import subprocess

from anthropic import AnthropicBedrock
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL = os.getenv("BEDROCK_MODEL_ID")
api_key = os.getenv("BEDROCK_API_KEY")
aws_region = os.getenv("AWS_REGION")

client = AnthropicBedrock(
    api_key = api_key,
    aws_region = aws_region,
)

SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."

TOOLS = [{
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    },
}]

# 执行bash命令的工具
def run_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "[ERROR]: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True,  cwd=os.getcwd(),
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "[no output]"
    except subprocess.TimeoutExpired:
        return "[Error]: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"[ERROR]:{e}"


def agent_loop(messages):
    while True:
        # 发起提问
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )

        # 大模型处理回复并累积
        messages.append({"role": "assistant", "content": response.content})

        # 判断是否使用工具
        if response.stop_reason != "tool_use":
            return
        
        # 使用工具，收集回复
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\033[33m$ {block.input['command']}\033[0m")
                output = run_bash(block.input["command"])
                print(output[:200])
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

        # 返回工具结果循环继续
        messages.append({"role": "user", "content": results})

if __name__ == "__main__":
    print("s01: Agent Loop")
    print("输入问题，回车发送。输入 q 退出。\n")
    history = []
    while True:
        try:
            query = input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        # Print the model's final text response
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if getattr(block, "type", None) == "text":
                    print(block.text)
        print()