#!/usr/bin/env bash
# simple-web-app의 고정 커밋을 F1 픽스처로 내보낸다.
set -euo pipefail
COMMIT="${1:-6050701}"
SRC="${SIMPLE_WEB_APP:-../simple-web-app}"
DEST="fixtures/f1-simple-web-app/repo"
rm -rf "$DEST"
mkdir -p "$DEST"
git -C "$SRC" archive "$COMMIT" | tar -x -C "$DEST"
echo "$COMMIT" > fixtures/f1-simple-web-app/SOURCE
