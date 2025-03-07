# -*- coding: UTF-8 -*-

from insights.client.apps.compliance import ComplianceClient, OSCAP_RESULTS_OUTPUT, COMPLIANCE_CONTENT_TYPE
from mock.mock import patch, MagicMock, Mock
from pytest import raises
from subprocess import PIPE, STDOUT


@patch("insights.client.config.InsightsConfig", base_url='localhost/app', systemid='', proxy=None)
def test_oscap_scan(config):
    compliance_client = ComplianceClient(config)
    compliance_client.get_policies = lambda: [{'attributes': {'ref_id': 'foo'}}]
    compliance_client.find_scap_policy = lambda ref_id: '/usr/share/xml/scap/foo.xml'
    compliance_client.run_scan = lambda ref_id, policy_xml: None
    payload, content_type = compliance_client.oscap_scan()
    assert payload == OSCAP_RESULTS_OUTPUT
    assert content_type == COMPLIANCE_CONTENT_TYPE


@patch("insights.client.config.InsightsConfig", base_url='localhost/app', systemid='', proxy=None)
def test_get_policies(config):
    compliance_client = ComplianceClient(config)
    compliance_client.hostname = 'foo'
    compliance_client.conn.session.get = Mock(return_value=Mock(status_code=200, json=Mock(return_value={'data': 'data'})))
    assert compliance_client.get_policies() == 'data'
    compliance_client.conn.session.get.assert_called_with('https://localhost/app/compliance/profiles', params={'hostname': 'foo'})


@patch("insights.client.config.InsightsConfig", base_url='localhost/app', systemid='', proxy=None)
def test_get_policies_error(config):
    compliance_client = ComplianceClient(config)
    compliance_client.hostname = 'foo'
    compliance_client.conn.session.get = Mock(return_value=Mock(status_code=500))
    assert compliance_client.get_policies() == []
    compliance_client.conn.session.get.assert_called_with('https://localhost/app/compliance/profiles', params={'hostname': 'foo'})


@patch("insights.client.config.InsightsConfig")
def test_os_release(config):
    compliance_client = ComplianceClient(config)
    assert int(compliance_client.os_release()) in range(6, 9)


@patch("insights.client.config.InsightsConfig")
def test_profile_files(config):
    compliance_client = ComplianceClient(config)
    compliance_client.os_release = lambda: '7'
    assert compliance_client.profile_files() == []


@patch("insights.client.apps.compliance.Popen")
@patch("insights.client.config.InsightsConfig")
def test_find_scap_policy(config, Popen):
    PATH = '/usr/share/xml/scap/ref_id.xml'
    Popen().wait = MagicMock(return_value=0)
    Popen().stdout.read = MagicMock(return_value=PATH.encode('utf-8'))
    compliance_client = ComplianceClient(config)
    compliance_client.profile_files = lambda: ['/something']
    assert compliance_client.find_scap_policy('ref_id') == PATH


@patch("insights.client.apps.compliance.Popen")
@patch("insights.client.config.InsightsConfig")
def test_find_scap_policy_not_found(config, Popen):
    Popen().wait = MagicMock(return_value=1)
    Popen().stderr.read = MagicMock(return_value='bad things happened')
    compliance_client = ComplianceClient(config)
    compliance_client.profile_files = lambda: ['/something']
    with raises(SystemExit):
        compliance_client.find_scap_policy('ref_id')


@patch("insights.client.apps.compliance.Popen")
@patch("insights.client.config.InsightsConfig")
def test_run_scan(config, Popen):
    Popen().wait = MagicMock(return_value=0)
    compliance_client = ComplianceClient(config)
    compliance_client.run_scan('ref_id', '/nonexistent')
    Popen.assert_called_with(["oscap", "xccdf", "eval", "--profile", 'ref_id', "--results", OSCAP_RESULTS_OUTPUT, '/nonexistent'], stdout=PIPE, stderr=STDOUT)


@patch("insights.client.apps.compliance.Popen")
@patch("insights.client.config.InsightsConfig")
def test_run_scan_fail(config, Popen):
    Popen().wait = MagicMock(return_value=1)
    Popen().stderr.read = MagicMock(return_value='bad things happened')
    compliance_client = ComplianceClient(config)
    with raises(SystemExit):
        compliance_client.run_scan('ref_id', '/nonexistent')
    Popen.assert_called_with(["oscap", "xccdf", "eval", "--profile", 'ref_id', "--results", OSCAP_RESULTS_OUTPUT, '/nonexistent'], stdout=PIPE, stderr=STDOUT)
