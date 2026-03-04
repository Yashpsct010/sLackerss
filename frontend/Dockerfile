FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# Production image
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV production

# Copy built assets
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Expose port
EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Note: server.js is created by next build automatically when output is set to 'standalone' in next.config.js
# If standalone is not enabled, use npm start
CMD ["npm", "start"]
