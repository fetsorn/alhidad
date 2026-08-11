#!/bin/bash
# Upload files from a sha256sum listing to S3, preserving file extension.
# Usage: publish-sha256.sh <listing> <root>
#   listing: sha256sum output file
#   root: directory the listing paths are relative to

LISTING="$1"
ROOT="$2"

if [ -z "$LISTING" ] || [ -z "$ROOT" ]; then
  echo "Usage: $0 <listing> <root>"
  exit 1
fi

while IFS='  ' read -r hash path; do
  ext="${path##*.}"
  key="sha256/$hash.$ext"
  if ! s3cmd info "s3://fetsorn/$key" &>/dev/null; then
    echo "uploading $key"
    s3cmd put "$ROOT/$path" "s3://fetsorn/$key" --acl-public
  else
    echo "exists $key"
  fi
done < "$LISTING"
