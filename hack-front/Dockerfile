# Стадия сборки
FROM node:22-alpine3.20 as build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm i

COPY . .

CMD ["npm", "start"]


# # Стадия запуска
# FROM nginx:alpine

# COPY nginx.conf    /etc/nginx/
# COPY build         /usr/share/nginx/html/

# EXPOSE 80

