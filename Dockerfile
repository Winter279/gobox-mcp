FROM python:3.12-slim

WORKDIR /app

# Install deps first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY gobox_auth.py gobox_client.py gobox_mcp.py ./
COPY tools/ ./tools/

EXPOSE 8000

ENV MCP_TRANSPORT=sse
ENV PORT=8000

CMD ["python", "gobox_mcp.py"]
