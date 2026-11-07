# Build stage. Base images are pinned by digest (multi-arch index current on 2026-10-14); Dependabot bumps them.
FROM node:24.22.2-alpine3.24@sha256:8a32c8cf649a49915a66e81e7a609223c708d0adabf288ee3f4077d765542f85 AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source code and build
COPY frontend/ .
RUN npm run build

# Production stage
FROM nginxinc/nginx-unprivileged:1.31.7-alpine3.24@sha256:b5047b9b76845eac124358373c6852377c52e4b05834a47647e955dd91cb8f1e

# Copy built assets to Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the server proxy configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# The unprivileged image listens on 8080 and runs as uid 101 (TCK-20261019-DEPLOY-DOCS-SHA-PINS-AND-FRONTEND-NONROOT)
USER 101
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
