#!/bin/bash

set -e
ROOT=$(realpath $(dirname $0))
cd "$ROOT"

if [ -z "$1" ]; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
else
    BRANCH=$1
fi

IMAGE=registry.gitlab.com/tech-squad3/hack-yolo-worker:$BRANCH

docker build . -t $IMAGE
docker push $IMAGE

echo "$IMAGE"
