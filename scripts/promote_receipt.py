"""Promotion validation entry point; obtains run metadata from GitHub API."""
import json
import os
import subprocess
from pathlib import Path
from .release_guard import validate_receipt

run_id = os.environ['DEVELOPMENT_RUN_ID']
if not run_id.isdigit():
    raise ValueError('Invalid run ID')
repo = os.environ['GITHUB_REPOSITORY']
run = json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/actions/runs/{run_id}']))
# Require the specific trusted development workflow, not an arbitrary successful job.
workflow = json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/actions/workflows/ci.yml']))
if run['workflow_id'] != workflow['id']:
    raise ValueError('Wrong workflow')
receipt = json.loads(Path('receipt/development.json').read_text())
image = validate_receipt(receipt, repo, run, run_id)
with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
    output.write('image='+image+'\nsha='+receipt['sha']+'\n')
