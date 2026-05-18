# Stage 1: Build the static frontend
FROM nginx:alpine AS frontend-builder
WORKDIR /usr/share/nginx/html

# Copy static HTML files
COPY signup.html ./
COPY index.html ./
COPY *.html ./

# Copy assets if any
COPY assets/ ./assets/ 2>/dev/null || true

# Stage 2: Build Pocketbase + Litestream
FROM golang:1.21-alpine AS pocketbase-builder
RUN go install github.com/pressly/litefs@latest

# Download Pocketbase binary (we'll pull from releases in CI)
# For now, we build or fetch during deploy
ARG POCKETBASE_VERSION=0.22.7
RUN wget -O /usr/local/bin/pocketbase https://github.com/pocketbase/pocketbase/releases/download/v${POCKETBASE_VERSION}/pocketbase_grpc_linux_amd64.zip && \
    unzip /usr/local/bin/pocketbase -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/pocketbase

# Final stage: Runtime
FROM alpine:3.19

RUN apk add --no-cache ca-certificates litestream

# Copy Pocketbase
COPY --from=pocketbase-builder /usr/local/bin/pocketbase /usr/local/bin/pocketbase

# Copy static frontend files for serving
COPY --from=frontend-builder /usr/share/nginx/html /usr/share/nginx/html

# Create Pocketbase data directory
RUN mkdir -p /pb/pb_data

# Install nginx for static file serving
RUN apk add --no-cache nginx

# Configure nginx to proxy API to Pocketbase and serve static files
COPY gcp/nginx.conf /etc/nginx/http.d/default.conf

# Entry point: start nginx, restore DB, replicate
COPY gcp/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]