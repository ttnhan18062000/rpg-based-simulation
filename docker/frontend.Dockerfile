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
FROM nginx:1.31.6-alpine3.24@sha256:df221db836e1754089190208cee7eeda94f233197056426eda74a43ab1abeac2

# Copy built assets to Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the server proxy configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port (Nginx default is 80)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
