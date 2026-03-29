FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package*.json /app/
RUN npm ci

COPY frontend /app

ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

FROM caddy:2-alpine

COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
