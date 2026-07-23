FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Note: This is an MCP stdio server. It does not listen on any network ports.
# It communicates entirely over standard input/output.
CMD ["python", "run.py"]
