#!/usr/bin/env bash
# 현재 VERSION 파일 기준으로 git 태그를 생성하고 push합니다.
# GitHub Actions가 자동으로 DMG를 빌드해 릴리스에 첨부합니다.
set -e

VERSION=$(cat VERSION | tr -d '[:space:]')
TAG="v${VERSION}"

if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "이미 존재하는 태그입니다: $TAG"
    exit 1
fi

echo "릴리스 태그 생성: $TAG"
git tag "$TAG"
git push origin "$TAG"
echo "✓ 완료 — GitHub Actions가 DMG를 빌드해 릴리스에 첨부합니다."
echo "  https://github.com/progh2/keep4mac/releases/tag/$TAG"
