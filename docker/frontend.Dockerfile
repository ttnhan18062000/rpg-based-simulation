# Build stage. Base images are pinned by digest (multi-arch index current on 2026-10-14); Dependabot bumps them.
FROM node:24.21.0-alpine3.24@sha256:ebfe2f90462722a7a4de65e91990e97fe0d401c70e0e762c5b53302f905ec1c1 AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source code and build
COPY frontend/ .
RUN npm run build

# Production stage
FROM nginxinc/nginx-unprivileged:1.31.6-alpine3.24@sha256:884e0b7f42f303641b0f4e78755aea647521dca0b89ca3be7992ad78b5c07434

# Copy built assets to Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the server proxy configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# The unprivileged image listens on 8080 and runs as uid 101 (TCK-20261019-DEPLOY-DOCS-SHA-PINS-AND-FRONTEND-NONROOT)
USER 101
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
