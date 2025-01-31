#!/usr/bin/env bash

set -o errexit
set -o nounset

# Determine if we're running in GitHub Actions or locally
if [ -n "${GITHUB_ACTIONS:-}" ]; then
    ROOT="${GITHUB_WORKSPACE}"
    IS_GITHUB_ACTIONS=true
else
    ROOT="$(git rev-parse --show-toplevel)"
    IS_GITHUB_ACTIONS=false
fi

VERSION_APP_PATH="${ROOT}/VERSION"
VERSION_DOCKER_PATH="${ROOT}/VERSION_DOCKER"
DOCKER_IMAGES_PATH="${ROOT}/DOCKER_IMAGES"

make_version() {
    GIT_SHA="$1"
    SHORT_SHA=$(echo "$GIT_SHA" | cut -c1-8)

    if [ "$IS_GITHUB_ACTIONS" = true ]; then
        BRANCH=${GITHUB_HEAD_REF:-${GITHUB_REF##*/}}
        TAG=$( [[ $GITHUB_REF == refs/tags/* ]] && echo "${GITHUB_REF##refs/tags/}" || echo "" )

        git fetch --tags --force
        git fetch --prune --unshallow || true
    else
        BRANCH=$(git rev-parse --abbrev-ref HEAD)
        TAG=$(git describe --exact-match --tags $GIT_SHA 2> /dev/null || echo "")
    fi

    LAST_RELEASE=$(get_last_release "$GIT_SHA")
    if [[ -n "$LAST_RELEASE" ]]; then
        VERSION_BASE="$LAST_RELEASE"
        LAST_RELEASE_HASH=$(git rev-list -n 1 "$LAST_RELEASE")
        GIT_COUNT=$(git rev-list --count "$LAST_RELEASE_HASH".."$GIT_SHA")
    else
        VERSION_BASE="0.1.0"
        GIT_COUNT="0"
    fi

    echo "GIT_SHA: $GIT_SHA"
    echo "SHORT_SHA: $SHORT_SHA"
    echo "BRANCH: $BRANCH"
    echo "TAG: $TAG"
    echo "VERSION_BASE: $VERSION_BASE"
    echo "GIT_COUNT: $GIT_COUNT"

    if [[ "$TAG" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        VERSION_APP="$TAG"
        VERSION_DOCKER="$TAG,${TAG}-${SHORT_SHA}"
    else
        BRANCH_TOKEN=$(echo "${BRANCH//[^a-zA-Z0-9-_.]/-}" | cut -c1-16 | sed -e 's/-$//')
        VERSION_APP="$VERSION_BASE+dev${GIT_COUNT}-${BRANCH_TOKEN}-${SHORT_SHA}"
        VERSION_DOCKER="$VERSION_APP"
    fi

    echo "APP VERSION: ${VERSION_APP}"
    echo "DOCKER VERSIONS: ${VERSION_DOCKER}"

    echo -n "${VERSION_APP}" > "${VERSION_APP_PATH}"
    echo -n "${VERSION_DOCKER}" > "${VERSION_DOCKER_PATH}"
}

get_last_release() {
    GIT_SHA="$1"
    LAST_RELEASE=$(git tag --list --merged "$GIT_SHA" --sort=-v:refname | grep -E "^[0-9]+\.[0-9]+\.[0-9]+$" | head -n 1)
    echo "$LAST_RELEASE"
}

make_docker_images_with_tags() {
    DOCKER_IMAGE_NAME="$1"
    DOCKER_IMAGE_TAGS=$(cat "${VERSION_DOCKER_PATH}")

    IFS=',' read -ra TAGS_ARRAY <<< "$DOCKER_IMAGE_TAGS"

    RESULT=""
    for TAG in "${TAGS_ARRAY[@]}"; do
        RESULT+="${DOCKER_IMAGE_NAME}:${TAG},"
    done

    RESULT=${RESULT%,}

    echo "DOCKER IMAGES WITH TAGS: ${RESULT}"

    echo -n "${RESULT}" > "${DOCKER_IMAGES_PATH}"
}

patch_versions_in_project_files() {
    PYPROJECT_PATH="${ROOT}/pyproject.toml"

    VERSION_APP=$(cat "${VERSION_APP_PATH}")

    sed -i "s#version = \"0.0.0\"#version = \"$VERSION_APP\"#" "${PYPROJECT_PATH}"
}

main() {
    GIT_SHA="$1"
    DOCKER_IMAGE_NAME="$2"

    make_version "$GIT_SHA"
    make_docker_images_with_tags "$DOCKER_IMAGE_NAME"
    patch_versions_in_project_files
}

main "$@"
