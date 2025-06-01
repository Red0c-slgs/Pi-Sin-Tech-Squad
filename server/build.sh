#!/bin/bash

set -e
ROOT=$(realpath $(dirname $0))
cd "$ROOT"

if [ -z "$1" ]; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
else
    BRANCH=$1
fi


##     RUN TESTS
#docker build . -f Dockerfile-test \
#               --build-arg USER=$USER \
#               --build-arg UID=$(id -u) \
#               --build-arg GID=$(id -g) \
#               -t cyntgoods-for-test
#
#
#mkdir ./pytest-report
#mkdir ./htmlcov
#UV_CMD="docker run -i --rm -v $(pwd)/src:/app/src -v $(pwd)/tests:/app/tests  -v $(pwd)/htmlcov:/app/htmlcov  -v $(pwd)/pytest-report:/app/pytest-report cyntgoods-for-test"
#echo ===============      ruff format       ===============
#$UV_CMD \
#    uv run ruff format src/
#
#echo ===============       ruff check       ===============
#$UV_CMD \
#    uv run ruff check src/
#
#echo ===============         pyright        ===============
#$UV_CMD \
#    uv tool run pyright
#
#echo ===============          pytest        ===============
#$UV_CMD \
#    uv run pytest tests/
#
#echo ===============      check coverage    ===============
#total_cov=$($UV_CMD uv run tests/check_pycov.py | tr -d '\r')
#
#if [[ "$total_cov" != "100" ]]; then
#    echo ""
#    echo "Ошибка: не полное тестовое покрытие: $total_cov%. Сборка остановлена."
#    exit 1
#fi

##     BUILD PRODUCTION IMAGE
SERVICE_NAME="server"
BRANCH_NAME_LOWER=$(echo "$BRANCH" | tr '[:upper:]' '[:lower:]')
BUILD_DATE=$(date +"%Y-%m-%dT%T")
BUILD_COMMIT_ID=$(git rev-parse HEAD)

cat > "$ROOT/src/version-info.json" <<EOF
{
    "component":"$SERVICE_NAME",
    "branch":"$BRANCH",
    "build_date":"$BUILD_DATE",
    "changeset":"$BUILD_COMMIT_ID"
}
EOF

IMAGE=registry.gitlab.com/tech-squad3/server:$BRANCH

docker build . -t $IMAGE
docker push $IMAGE

echo "$IMAGE"
