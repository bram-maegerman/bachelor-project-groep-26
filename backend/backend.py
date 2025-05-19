import subprocess
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

def run_script():
    process = subprocess.Popen(
        ["python", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    for line in iter(process.stdout.readline, ''):
        yield line
    process.stdout.close()
    process.wait()

@app.get("/check-numbers")
def check_numbers():
    return StreamingResponse(run_script(), media_type="text/plain")