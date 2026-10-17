# Verif-AI backend for AWS Lambda (container image + Lambda Web Adapter).
# Build from the backend/ directory:  docker build -t verfai-backend .
FROM python:3.11-slim

COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    AWS_LWA_PORT=8080 \
    AWS_LWA_READINESS_CHECK_PATH=/api/health/ \
    AWS_LWA_INVOKE_MODE=buffered

WORKDIR /app

# torch / transformers / safetensors are only for the local safetensors path, so skip them here.
# The BERT classifier ships as an ONNX file in models/onnx (copied with the code below).
COPY requirements.txt .
RUN grep -viE '^(torch|transformers|safetensors)' requirements.txt > /tmp/requirements-lambda.txt \
    && pip install -r /tmp/requirements-lambda.txt

COPY . .

EXPOSE 8080
# One worker/thread pool sized for Lambda's single-request-per-instance model.
CMD ["gunicorn", "verfai.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120"]
