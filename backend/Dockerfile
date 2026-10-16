# Verif-AI backend for AWS Lambda (container image + Lambda Web Adapter).
# Build from the backend/ directory:  docker build -t verfai-backend .
FROM python:3.11-slim

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf \
    AWS_LWA_PORT=8080 \
    AWS_LWA_READINESS_CHECK_PATH=/api/health/ \
    AWS_LWA_INVOKE_MODE=buffered

WORKDIR /app

# CPU-only torch keeps the image small; the rest comes from requirements.txt.
COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

# Bake the BERT model into the image so cold starts never download it.
# Pass a token only if the model repo is private:  --secret id=hf_token,src=hf_token.txt
ARG BAKE_MODEL=true
RUN --mount=type=secret,id=hf_token \
    if [ "$BAKE_MODEL" = "true" ]; then \
      export HF_TOKEN="$(cat /run/secrets/hf_token 2>/dev/null || true)"; \
      python -c "from huggingface_hub import snapshot_download; snapshot_download('ManokManokManok/bimBert_Scam-Detection')"; \
    fi
ENV HF_HUB_OFFLINE=1

COPY . .

EXPOSE 8080
# One worker/thread pool sized for Lambda's single-request-per-instance model.
CMD ["gunicorn", "verfai.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120"]
