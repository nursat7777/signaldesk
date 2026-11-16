"""Validate immutable promotion receipts; never accept a mutable tag."""
import re


def validate_receipt(receipt, repository, run, expected_run_id):
    image = receipt.get('image', '')
    prefix = 'ghcr.io/'+repository.lower()+'@sha256:'
    if not image.startswith(prefix) or not re.fullmatch(r'[a-f0-9]{64}', image[len(prefix):]):
        raise ValueError('Expected repository-bound immutable digest')
    if run.get('conclusion') != 'success' or run.get('head_branch') != 'develop' or run.get('event') != 'push':
        raise ValueError('Development deployment did not pass')
    if receipt.get('environment') != 'development' or receipt.get('run_id') != int(expected_run_id):
        raise ValueError('Receipt is not for this development run')
    if not re.fullmatch(r'[a-f0-9]{40}', receipt.get('sha', '')) or receipt['sha'] != run.get('head_sha'):
        raise ValueError('Commit mismatch')
    if receipt.get('smoke_passed') is not True:
        raise ValueError('Development smoke tests missing')
    return image
