FROM python:3.11-slim

RUN apt-get update && apt-get install -y git curl tmux && rm -rf /var/lib/apt/lists/*
RUN pip install fastapi uvicorn

WORKDIR /workspace
COPY sandbox_api.py /app/sandbox_api.py

WORKDIR /app
CMD ["uvicorn", "sandbox_api:app", "--host", "0.0.0.0", "--port", "8000"]
