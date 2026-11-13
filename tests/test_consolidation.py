import json
from pathlib import Path

import pytest
import yaml

from controller import monitor, status
from controller.github_actions import GitHubActionsError, dispatch_workflow
from test_status import _write_fixture


def test_disabled_and_closed_projects_never_monitor_or_dispatch(tmp_path, monkeypatch):
    root = _write_fixture(tmp_path, enabled=False)
    config_path = root / 'projects.yaml'
    registry = yaml.safe_load(config_path.read_text())
    registry['projects']['example']['monitor'] = {'enabled': True, 'kind': 'github_actions_workflows'}
    config_path.write_text(yaml.safe_dump(registry))
    def forbidden(*args, **kwargs):
        raise AssertionError('closed project contacted a remote service')
    monkeypatch.setattr(monitor, 'monitor_project', forbidden)
    monkeypatch.setattr(status, 'github_branch_sha', forbidden)
    assert monitor.run_monitors(root, token='test', allow_scheduler_recovery=True)['observations'] == []
    assert status.build_report(root, verify_remote=True, token='test')['ok'] is True
    registry['projects']['example']['enabled'] = True
    config_path.write_text(yaml.safe_dump(registry))
    state_path = root / 'state/example.json'
    state = json.loads(state_path.read_text())
    state['lifecycle_status'] = 'CLOSED'
    state_path.write_text(json.dumps(state))
    assert monitor.run_monitors(root, token='test', allow_scheduler_recovery=True)['observations'] == []


@pytest.mark.parametrize('workflow', ['forward-paper-cycle.yml', 'forward-challengers.yml',
                                     'forward-paper-health.yml', 'forward-challenger-health.yml',
                                     'critical-runtime-smoke.yml'])
def test_all_retired_btc_recovery_dispatches_are_denied(workflow):
    with pytest.raises(GitHubActionsError, match='Closed research'):
        dispatch_workflow('williammolina489/crypto-trading-bot', workflow, 'main', 'unused')


def test_closed_funding_dispatch_is_denied_for_every_workflow():
    with pytest.raises(GitHubActionsError, match='Closed research'):
        dispatch_workflow('williammolina489/crypto-funding-basis-bot', 'anything.yml', 'main', 'unused')


def test_historical_one_off_runners_have_no_execution_path():
    for name in ['oct1-recovery-dispatch', 'e002-finite-checkpoints', 'crypto-e002-read-only']:
        text = Path(f'.github/workflows/{name}.yml').read_text()
        assert 'if: ${{ false }}' in text.split('\njobs:', 1)[1]
    registry = yaml.safe_load(Path('projects.yaml').read_text())
    config = registry['projects']['crypto_trading_bot']['monitor']
    assert config['workflows'] == ['EXP-010 mean reversion paper']
    assert config['scheduler_recovery']['enabled'] is False
