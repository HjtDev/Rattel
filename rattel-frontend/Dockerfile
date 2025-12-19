FROM node:25.2.1-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install --only=production=false

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]