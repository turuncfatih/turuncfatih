#!/usr/bin/env bash
# Re-download the devicon logos that build_stack.py embeds.
set -euo pipefail
D="https://cdn.jsdelivr.net/gh/devicons/devicon/icons"
OUT="$(dirname "$0")/logos"
mkdir -p "$OUT"
for spec in \
  dotnetcore/dotnetcore-original nodejs/nodejs-original typescript/typescript-original \
  react/react-original expo/expo-original microsoftsqlserver/microsoftsqlserver-plain \
  postgresql/postgresql-original mongodb/mongodb-original firebase/firebase-plain \
  supabase/supabase-original redis/redis-original elasticsearch/elasticsearch-original \
  azure/azure-original amazonwebservices/amazonwebservices-plain-wordmark \
  cloudflare/cloudflare-original docker/docker-original
do
  curl -sf "$D/$spec.svg" -o "$OUT/$(basename "$spec").svg" && echo "  ok $(basename "$spec")"
done
