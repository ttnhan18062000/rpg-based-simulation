# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy source code and build
COPY frontend/ .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets to Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the server proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port (Nginx default is 80)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
