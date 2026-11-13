"""Copy every currently downloadable artifact to a permanent release. Never delete."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time
import zipfile


def gh(*args):
    for attempt in range(4):
        result = subprocess.run(['gh', *args], capture_output=True)
        if result.returncode == 0:
            return result.stdout
        if attempt < 3:
            time.sleep(2 ** attempt)
    raise RuntimeError(f'GitHub operation failed: {args[:2]} (details withheld: signed URLs)')


def json_pages(raw):
    pages = []
    raw = raw.decode()
    while raw.strip():
        raw = raw.lstrip()
        page, end = json.JSONDecoder().raw_decode(raw)
        pages.append(page)
        raw = raw[end:]
    return pages


def main():
    repo = os.environ['GITHUB_REPOSITORY']
    run = os.environ['GITHUB_RUN_ID']
    root = Path('evidence-archive')
    root.mkdir(exist_ok=True)
    pages = json_pages(gh('api', f'repos/{repo}/actions/artifacts?per_page=100', '--paginate'))
    artifacts = [a for page in pages for a in page['artifacts']]
    (root / 'inventory.json').write_text(json.dumps(artifacts, indent=2))

    def download(a):
        if a['expired']:
            return {'id': a['id'], 'expired_before_archive': True}
        data = gh('api', f"repos/{repo}/actions/artifacts/{a['id']}/zip")
        path = root / f"{a['id']}.zip"
        path.write_bytes(data)
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise RuntimeError(f"Invalid ZIP {a['id']}")
        return {'id': a['id'], 'name': a['name'], 'run_id': a['workflow_run']['id'],
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    with ThreadPoolExecutor(max_workers=4) as pool:
        manifest = list(pool.map(download, artifacts))
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    output = Path('actions-evidence.tar.gz')
    with tarfile.open(output, 'w:gz') as archive:
        archive.add(root, arcname='evidence')
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    Path('SHA256SUMS').write_text(f'{checksum}  {output.name}\n')
    tag = f'evidence-preservation-{run}'
    notes = Path('evidence-notes.md')
    notes.write_text(f'Preserves {len(manifest)} artifact inventory records from {repo}. '
                     'Original ZIP bytes, source run IDs, expiry metadata and SHA-256 hashes are included. '
                     'Expired artifacts are explicitly recorded as unavailable. No research execution or deletion.\n')
    gh('release', 'create', tag, '--repo', repo, '--target', os.environ['GITHUB_SHA'],
       '--title', f'Research evidence preservation {run}', '--notes-file', str(notes),
       str(output), 'SHA256SUMS', str(root / 'manifest.json'), str(root / 'inventory.json'))
    release = json.loads(gh('api', f'repos/{repo}/releases/tags/{tag}'))
    sizes = {a['name']: a['size'] for a in release['assets']}
    for path in [output, Path('SHA256SUMS'), root / 'manifest.json', root / 'inventory.json']:
        if sizes.get(path.name) != path.stat().st_size:
            raise RuntimeError(f'Release asset verification failed: {path.name}')
    print(f"Verified permanent archive: {release['html_url']}; SHA256 {checksum}")


if __name__ == '__main__':
    main()
