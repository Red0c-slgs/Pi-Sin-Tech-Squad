#!/bin/bash

set -e
ROOT=$(realpath $(dirname $0))
cd "$ROOT"

if [ -z "$1" ]; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
else
    BRANCH=$1
fi

##     BUILD PRODUCTION IMAGE
SERVICE_NAME="front"
BRANCH_NAME_LOWER=$(echo "$BRANCH" | tr '[:upper:]' '[:lower:]')
BUILD_DATE=$(date +"%Y-%m-%dT%T")
BUILD_COMMIT_ID=$(git rev-parse HEAD)

IMAGE=registry.gitlab.com/tech-squad3/hack-front:$BRANCH

docker build . -t $IMAGE
docker push $IMAGE

echo "$IMAGE"