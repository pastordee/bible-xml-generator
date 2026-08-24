#!/bin/bash
# Publish the packaged Bible archives to Cloudflare R2.
#
# This is the step that was missing: package_all.sh produced the zips, but
# getting them onto R2 was done by hand through the Cloudflare console, so
# repaired data could sit in readyForServer/ for a long time while the app went
# on serving the old files.
#
#   ./publish_to_r2.sh --dry-run   # show what would change, upload nothing
#   ./publish_to_r2.sh             # upload, then verify against the live CDN
#
# Credentials are read from the Parse server's /root/.env over SSH and passed to
# rclone as environment variables. Nothing is written to
# ~/.config/rclone/rclone.conf — the R2 secret stays off this machine's disk.

set -euo pipefail

SERVER="root@172.104.27.182"
SSH_KEY="$HOME/.ssh/prayer_circle_id"
SOURCE_DIR="readyForServer"
PREFIX="app_assets"
CDN="https://media.prayercircle.co.uk/${PREFIX}"

cd "$(dirname "$0")"

command -v rclone >/dev/null || { echo "✗ rclone not installed (brew install rclone)"; exit 1; }
[ -d "$SOURCE_DIR" ] || { echo "✗ $SOURCE_DIR not found — run ./package_all.sh first"; exit 1; }

echo "Reading R2 credentials from ${SERVER}…"
CREDS=$(ssh -o BatchMode=yes -i "$SSH_KEY" "$SERVER" \
  'set -a; . /root/.env 2>/dev/null; set +a; printf "%s\n%s\n%s\n%s\n" \
   "$R2_ACCESS_KEY_ID" "$R2_SECRET_ACCESS_KEY" "$R2_ENDPOINT" "$R2_BUCKET_NAME"')

AK=$(echo "$CREDS" | sed -n 1p)
SK=$(echo "$CREDS" | sed -n 2p)
EP=$(echo "$CREDS" | sed -n 3p)
BK=$(echo "$CREDS" | sed -n 4p)

[ -n "$AK" ] && [ -n "$SK" ] && [ -n "$EP" ] && [ -n "$BK" ] || {
  echo "✗ Could not read R2 credentials from the server's /root/.env"; exit 1; }

export RCLONE_CONFIG_R2_TYPE=s3
export RCLONE_CONFIG_R2_PROVIDER=Cloudflare
export RCLONE_CONFIG_R2_ACCESS_KEY_ID="$AK"
export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$SK"
export RCLONE_CONFIG_R2_ENDPOINT="$EP"
export RCLONE_CONFIG_R2_NO_CHECK_BUCKET=true

INCLUDES=(--include "xml_*.zip" --include "xml_*.zip.hash"
          --include "*_dictionary.zip" --include "*_dictionary.zip.hash")

echo "Bucket: $BK/$PREFIX"
echo

if [ "${1:-}" = "--dry-run" ]; then
  echo "=== DRY RUN — nothing will be uploaded ==="
  rclone copy "$SOURCE_DIR/" "R2:$BK/$PREFIX/" "${INCLUDES[@]}" --dry-run -v 2>&1 \
    | grep -E "Skipped copy|Skipped update" | sed 's/^.*NOTICE: /  /' || true
  echo
  echo "'Skipped copy' = content changed and would be uploaded."
  echo "'Skipped update modification time' = identical, only the timestamp differs."
  exit 0
fi

echo "=== Uploading ==="
rclone copy "$SOURCE_DIR/" "R2:$BK/$PREFIX/" "${INCLUDES[@]}" -v --stats-one-line 2>&1 \
  | grep -E "Copied|Transferred:" | tail -20 || true
# `|| true`: with everything already published the grep matches nothing
# and exits 1, which under `set -e -o pipefail` killed the script before
# it reached the verification step — the part that matters most.
echo "  (no lines above means every file was already up to date)"

echo
echo "=== Verifying against the live CDN ==="
# The app compares the published .hash against its local copy, so a zip whose
# hash did not also upload would leave clients on the old data forever.
fail=0
for zip in "$SOURCE_DIR"/xml_*.zip; do
  name=$(basename "$zip")
  local_md5=$(md5 -q "$zip")
  published=$(curl -fsS "$CDN/${name}.hash" 2>/dev/null | tr -d '[:space:]' || echo "")
  if [ "$local_md5" = "$published" ]; then
    printf "  ✓ %-22s %s\n" "$name" "${published:0:12}…"
  else
    printf "  ✗ %-22s local=%s published=%s\n" "$name" "${local_md5:0:12}…" "${published:0:12}…"
    fail=1
  fi
done

echo
if [ "$fail" -eq 0 ]; then
  echo "✓ Published. Every archive's hash matches what the CDN serves."
else
  echo "✗ Some hashes do not match — clients will not pick up those versions."
  exit 1
fi
