# Semantic Modeling Assistant — mock UI
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Empty / same-origin: the UI calls <BASE_PATH>/api and nginx in this image
# proxies /api to the backend.
ARG VITE_API_BASE_URL=same-origin
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# The base path is a placeholder replaced at container start (docker-base-path.sh).
RUN printf 'VITE_API_BASE_URL=%s\n' "$VITE_API_BASE_URL" > .env.production \
    && npm run build -- --base=/__SLOVNIKY_AI_BASE_PATH__/

FROM nginx:1.27-alpine

# Public URL path the UI is served under, e.g. /slovniky-ai. Empty = site root.
# A reverse proxy in front must strip this prefix before forwarding here.
ENV BASE_PATH=

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html-template
COPY --chmod=755 docker-base-path.sh /docker-entrypoint.d/40-slovniky-base-path.sh

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
