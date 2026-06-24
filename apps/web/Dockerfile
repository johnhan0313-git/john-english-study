FROM node:20-alpine AS base

FROM base AS deps
ARG GITHUB_TOKEN
WORKDIR /app
COPY package.json package-lock.json ./
COPY packages/api-client/package.json ./packages/api-client/
COPY packages/app-core/package.json ./packages/app-core/
COPY apps/web/package.json ./apps/web/
RUN printf '@johnhan0313-git:registry=https://npm.pkg.github.com\n//npm.pkg.github.com/:_authToken=%s\n' "$GITHUB_TOKEN" > .npmrc \
    && npm ci --workspace=@sceneenglish/web --include-workspace-root

FROM base AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/web/node_modules ./apps/web/node_modules
COPY package.json package-lock.json ./
COPY packages ./packages
COPY apps/web ./apps/web
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app/apps/web
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
COPY --from=builder /app/apps/web/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
