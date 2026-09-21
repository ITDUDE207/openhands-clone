import os
import sys
import json
import requests
from openai import OpenAI

# Initialize client using Groq cloud configurations
client = OpenAI(
    base_url="https://groq.com",
    api_key=os.getenv("GROQ_API_KEY")
)

SANDBOX_URL = os.getenv("SANDBOX_URL", "http://localhost:8000")
WORKSPACE_DIR = "/workspace"
MODEL_NAME = "llama-3.3-70b-versatile" 

SYSTEM_PROMPT = """You are an autonomous AI software engineer. Your goal is to solve the user's task.
You have access to two capabilities:
1. Run a bash command in a secure sandbox.
2. Write/overwrite a file in the workspace.

You MUST respond strictly in a raw JSON object format so your parsing engine can read it. 
Do not wrap your answer in markdown code blocks like ```json ... ```. Just return raw JSON.

If you need to run a command:
{
    "thought": "I need to check the current directory contents.",
    "action": "RunCommand",
    "command": "ls -la"
}

If you need to create or update a file:
{
    "thought": "I will create a basic app file.",
    "action": "WriteFile",
    "path": "app.py",
    "content": "print('Hello World')"
}

If you are completely finished with the task:
{
    "thought": "I have completed everything successfully.",
    "action": "Complete",
    "message": "The app has been built and tested successfully."
}
"""

def handle_action(action_json):
    action = action_json.get("action")
    
    if action == "RunCommand":
        cmd = action_json.get("command")
        print(f"🤖 [Agent]: Executing command -> {cmd}")
        res = requests.post(f"{SANDBOX_URL}/exec", json={"command": cmd}).json()
        return f"Exit Code: {res['exit_code']}\nSTDOUT:\n{res['stdout']}\nSTDERR:\n{res['stderr']}"
        
    elif action == "WriteFile":
        rel_path = action_json.get("path")
        content = action_json.get("content")
        full_path = os.path.join(WORKSPACE_DIR, rel_path)
        
        print(f"🤖 [Agent]: Writing file -> {rel_path}")
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)
        return f"Successfully wrote file to {rel_path}"
        
    return "Unknown action."

def clean_and_parse_json(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())

def run_agent(user_prompt):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    print(f"🚀 Starting task via Groq Cloud Cloud Engine ({MODEL_NAME})\n" + "="*50)
    
    for iteration in range(15):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            response_text = response.choices.message.content
            action_data = clean_and_parse_json(response_text)
            
            print(f"\n🧠 [Thought]: {action_data.get('thought')}")
            
            if action_data.get("action") == "Complete":
                print(f"✅ [Finished]: {action_data.get('message')}")
                break
                
            tool_output = handle_action(action_data)
            
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"Observation from previous action:\n{tool_output}"})
            
        except Exception as e:
            print(f"❌ Error in agent loop: {e}")
            break

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY") or "your_actual_free_groq_key" in os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY environment variable not configured properly inside your .env file.")
        sys.exit(1)
        
    task = input("What software engineering task should I do? ")
    run_agent(task)
