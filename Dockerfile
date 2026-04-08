FROM python:3.12-slim

WORKDIR /app

# Copy project metadata + source
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install package (installs deps + console script `gobox-mcp`)
RUN pip install --no-cache-dir .

EXPOSE 8000

ENV MCP_TRANSPORT=sse
ENV PORT=8000

CMD ["gobox-mcp"]
