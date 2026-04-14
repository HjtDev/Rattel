FROM node:25.6.1-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./

RUN npm config set registry https://npm.devneeds.ir
RUN npm ci

FROM node:25.6.1-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Build step would go here for production

FROM node:25.2.1-slim
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
