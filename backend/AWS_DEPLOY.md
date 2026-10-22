# Deploying Verif-AI backend to AWS Lambda

Cost model: Lambda bills per request and per GB-second only while a request runs. Idle = ~$0
(plus ~$0.10/month ECR storage for the image). Check current free-tier numbers on the AWS pricing page.

## One-time setup
1. Create an AWS account, then install the AWS CLI, SAM CLI and Docker. Run `aws configure`.
2. Gmail: Google Account > Security > 2-Step Verification > App passwords. Make a 16-character password.
   Never paste it in chat; it only goes into the deploy command below.
3. MongoDB Atlas > Network Access: allow `0.0.0.0/0` (Lambda has no fixed IP). Keep the DB user password strong.

## Build and push the image (from `backend/`)
```
aws ecr create-repository --repository-name verfai-backend --region us-east-1
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
docker build -t verfai-backend .
docker tag verfai-backend:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/verfai-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/verfai-backend:latest
```
If the Hugging Face model repo is private, build with
`docker build --secret id=hf_token,src=hf_token.txt -t verfai-backend .`.

## Deploy
```
sam deploy --stack-name verfai --region us-east-1 --capabilities CAPABILITY_IAM --resolve-s3 --guided
```
Answer the prompts: ImageUri, FrontendOrigin (the canonical Vercel URL), BudgetEmail, and the secrets
(DjangoSecretKey, JwtSecretKey, MongoUri, GeminiApiKey, EmailUser, EmailAppPassword). The template
also allows the previous `https://verif-ai-frontend.vercel.app` origin for compatibility, while
frontend links use the canonical URL. The output `ApiUrl` goes into Vercel as `VITE_API_BASE_URL`,
then redeploy the frontend.
If you use a region other than us-east-1, edit `DJANGO_ALLOWED_HOSTS` in `template.yaml`.

## Failsafes built in
- New AWS accounts are limited to 5 concurrent runs account-wide, which also caps cost and Gemini usage.
  (Reserved concurrency is not allowed on such accounts, so the template doesn't use it.)
- AWS Budget: emails you at 80% actual and 100% forecast of `MonthlyBudgetUsd` (default $5).
- App-level rate limits stored in Mongo (`RATE_LIMIT_ENABLED=true`).

## Turn OFF / ON (the URL stays the same; allow ~20 s to take effect)
- OFF (public requests get 403, nothing runs):
  `aws lambda update-function-url-config --function-name <FunctionName> --auth-type AWS_IAM --region us-east-1`
- ON:
  `aws lambda update-function-url-config --function-name <FunctionName> --auth-type NONE --region us-east-1`
- Delete everything: `sam delete --stack-name verfai`.
Find the function name with `aws lambda list-functions --query "Functions[].FunctionName"`.

## Notes
- New accounts cap Lambda memory at 512 MB. The ONNX model needs about 1 GB: once AWS lifts the cap
  (automatically with usage, or via a Service Quotas request), redeploy with `MemoryMb=1024`.
- Gemini free tier is only ~20 requests/day per model; the app falls back through the other configured models.
  Enable billing on the Gemini key if you expect real traffic.
- The first request after idle takes ~10-20 s (cold start). Later requests are fast.
- Anonymous (guest) chatbot history is kept in instance memory and can reset between Lambda instances.
- Redeploy after pushing a new image: `sam deploy` with the new ImageUri (use a new tag).
