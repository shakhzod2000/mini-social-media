# --------- Multi-stage build -----------

# ---------- Stage 1: builder ----------
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements/base.txt requirements/base.txt

# Install deps to /install
RUN pip install --no-cache-dir --prefix=/install -r requirements/base.txt

# ---------- Stage 2: runtime ----------

# The runtime stage only gets the compiled packages, not all that build junk. Result = smaller image

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy ONLY the installed packages
COPY --from=builder /install /usr/local

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
