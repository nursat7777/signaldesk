import pytest
from scripts.release_guard import validate_receipt


def valid():
    return {'image': 'ghcr.io/example/signaldesk@sha256:'+'a'*64, 'environment': 'development', 'sha': 'b'*40, 'run_id': 123, 'smoke_passed': True}, {'conclusion': 'success', 'head_branch': 'develop', 'event': 'push', 'head_sha': 'b'*40}


def test_exact_tested_digest():
    receipt, run = valid()
    assert validate_receipt(receipt, 'Example/SignalDesk', run, '123') == receipt['image']


@pytest.mark.parametrize('field,value', [('image', 'ghcr.io/example/signaldesk:latest'), ('image', 'ghcr.io/attacker/signaldesk@sha256:'+'a'*64), ('environment', 'production'), ('sha', 'c'*40), ('run_id', 124), ('smoke_passed', False)])
def test_reject_untrusted_receipt(field, value):
    receipt, run = valid()
    receipt[field] = value
    with pytest.raises(ValueError):
        validate_receipt(receipt, 'example/signaldesk', run, 123)


@pytest.mark.parametrize('field,value', [('conclusion', 'failure'), ('head_branch', 'main'), ('event', 'pull_request')])
def test_reject_untested_or_wrong_source(field, value):
    receipt, run = valid()
    run[field] = value
    with pytest.raises(ValueError):
        validate_receipt(receipt, 'example/signaldesk', run, 123)
