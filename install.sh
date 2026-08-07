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
source_dir="$repo_root/neoforge-dev"
skills_dir="${CODEX_HOME:-$HOME/.codex}/skills"
target_dir="$skills_dir/neoforge-dev"

if [[ ! -f "$source_dir/SKILL.md" || ! -f "$source_dir/agents/openai.yaml" ]]; then
  printf 'Invalid package: required skill files are missing.\n' >&2
  exit 1
fi

mkdir -p "$skills_dir"

if [[ -e "$target_dir" ]]; then
  if [[ "$force" != true ]]; then
    printf 'Target already exists: %s\nRe-run with --force to replace it and retain a backup.\n' "$target_dir" >&2
    exit 1
  fi

  timestamp="$(date +%Y%m%d-%H%M%S)"
  backup_dir="$target_dir.backup-$timestamp"
  mv "$target_dir" "$backup_dir"
  printf 'Existing installation moved to %s\n' "$backup_dir"
fi

cp -R "$source_dir" "$target_dir"
printf 'Installed neoforge-dev to %s\n' "$target_dir"
printf 'The skill will be available from the next Codex turn.\n'
