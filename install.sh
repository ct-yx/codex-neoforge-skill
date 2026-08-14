#!/usr/bin/env bash
set -euo pipefail

force=false
if [[ "${1:-}" == "--force" ]]; then
  force=true
elif [[ $# -gt 0 ]]; then
  printf 'Usage: %s [--force]\n' "$0" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$repo_root/minecraft-mod-dev"
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
target_dir="$skills_dir/minecraft-mod-dev"

if [[ ! -f "$source_dir/SKILL.md" || ! -f "$source_dir/agents/openai.yaml" ]]; then
  printf 'Invalid package: required skill files are missing.\n' >&2
  exit 1
fi

mkdir -p "$skills_dir"

staging_dir="$(mktemp -d "$skills_dir/.minecraft-mod-dev.staging.XXXXXX")"
trap 'rm -rf "$staging_dir"' EXIT
cp -R "$source_dir" "$staging_dir/minecraft-mod-dev"

if [[ ! -f "$staging_dir/minecraft-mod-dev/SKILL.md" || ! -f "$staging_dir/minecraft-mod-dev/agents/openai.yaml" ]]; then
  printf 'Staging package validation failed.\n' >&2
  exit 1
fi

backup_dir=""
if [[ -e "$target_dir" || -L "$target_dir" ]]; then
  if [[ "$force" != true ]]; then
    printf 'Target already exists: %s\nRe-run with --force to replace it and retain a backup.\n' "$target_dir" >&2
    exit 1
  fi

  timestamp="$(date +%Y%m%d-%H%M%S)"
  backup_dir="$target_dir.backup-$timestamp"
  suffix=1
  while [[ -e "$backup_dir" || -L "$backup_dir" ]]; do
    backup_dir="$target_dir.backup-$timestamp-$suffix"
    suffix=$((suffix + 1))
  done
  mv "$target_dir" "$backup_dir"
  printf 'Existing installation moved to %s\n' "$backup_dir"
fi

mv "$staging_dir/minecraft-mod-dev" "$target_dir"
printf 'Installed minecraft-mod-dev to %s\n' "$target_dir"
printf 'The skill will be available from the next Codex turn.\n'
