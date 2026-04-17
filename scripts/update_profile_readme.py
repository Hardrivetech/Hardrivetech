#!/usr/bin/env python3
import os
import json
import sys
import urllib.request
from pathlib import Path


def fetch_repos(owner, token=None):
    url = f'https://api.github.com/users/{owner}/repos?per_page=100&type=owner'
    headers = {'User-Agent': 'github-profile-update-script'}
    if token:
        headers['Authorization'] = f'token {token}'
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def format_repo_list(repos, owner, limit=6):
    repos = [r for r in repos if not r.get('fork') and not r.get('archived')]
    repos.sort(key=lambda r: (r.get('stargazers_count', 0), r.get('pushed_at') or ''), reverse=True)
    lines = []
    for r in repos[:limit]:
        name = r.get('name')
        desc = (r.get('description') or '').replace('\n', ' ').strip()
        lang = r.get('language') or ''
        stars = r.get('stargazers_count', 0)
        lang_part = f' · `{lang}`' if lang else ''
        lines.append(f"- [{name}](https://github.com/{owner}/{name}) — {desc}{lang_part} · ⭐ {stars}")
    return "\n".join(lines)


def main():
    repo_env = os.environ.get('GITHUB_REPOSITORY', '')
    owner = repo_env.split('/')[0] if repo_env else os.environ.get('GITHUB_ACTOR', 'Hardrivetech')
    token = os.environ.get('GITHUB_TOKEN')

    try:
        repos = fetch_repos(owner, token)
    except Exception as e:
        print('Failed to fetch repos:', e)
        sys.exit(1)

    repo_list_md = format_repo_list(repos, owner)

    template_path = Path('profile/README.template.md')
    if not template_path.exists():
        print('Template not found at', template_path)
        sys.exit(1)

    template = template_path.read_text(encoding='utf-8')
    start_marker = '<!-- REPO_LIST_START -->'
    end_marker = '<!-- REPO_LIST_END -->'
    start_i = template.find(start_marker)
    end_i = template.find(end_marker)

    if start_i == -1 or end_i == -1 or end_i < start_i:
        print('Template markers not found or malformed')
        sys.exit(1)

    start_i += len(start_marker)
    new_content = template[:start_i] + '\n\n' + repo_list_md + '\n\n' + template[end_i:]

    out = Path('README.md')
    out.write_text(new_content, encoding='utf-8')
    print('Generated README.md')


if __name__ == '__main__':
    main()
