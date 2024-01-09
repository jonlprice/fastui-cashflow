docker buildx build --platform=linux/amd64 -t fastapi-amd64:1.0 .

docker buildx build -t fastapi:1.0 .

docker build -t fastapi .

docker run -d -name fastapi -p 80:80 fastapi
