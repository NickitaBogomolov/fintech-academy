FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY toolchain/solc/package.json toolchain/solc/package-lock.json toolchain/solc/
RUN cd toolchain/solc && npm ci --omit=dev --no-audit --no-fund
COPY toolchain toolchain

COPY pyproject.toml ./
COPY dfa_studio dfa_studio
RUN pip install --no-cache-dir ".[analysis]"

ENV DFA_DATA_DIR=/data \
    DFA_SOLC_DIR=/app/toolchain/solc \
    PYTHONUNBUFFERED=1

VOLUME /data
EXPOSE 8000

CMD ["uvicorn", "dfa_studio.api:app", "--host", "0.0.0.0", "--port", "8000"]
