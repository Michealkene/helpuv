# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Build arguments for Vite env vars
ARG VITE_API_URL=https://api.helpuvio.com
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_PAYSTACK_PUBLIC_KEY

# Set as environment variables for the build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_PAYSTACK_PUBLIC_KEY=$VITE_PAYSTACK_PUBLIC_KEY

# Copy package files
COPY package.json ./

# Install dependencies (use npm install instead of npm ci)
RUN npm install

# Copy source
COPY . .

# Build app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]