import subprocess
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class CommandRequest(BaseModel):
    command: str

@app.post("/exec")
def execute_command(req: CommandRequest):
    try:
        res = subprocess.run(
            req.command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30, 
            cwd="/workspace"
        )
        return {
            "stdout": res.stdout, 
            "stderr": res.stderr, 
            "exit_code": res.returncode
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Error: Command timed out after 30 seconds.", "exit_code": 124}
