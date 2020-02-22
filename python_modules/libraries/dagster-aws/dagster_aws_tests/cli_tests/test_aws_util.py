import io

import boto3
from dagster_aws.cli.aws_util import get_validated_ami_id, select_region
from dagster_aws.cli.config import EC2Config
from moto import mock_ec2


def test_select_region(monkeypatch, capsys):
    region = 'us-east-1'
    monkeypatch.setattr(
        'sys.stdin', io.StringIO('does-not-exist\n{region}\n'.format(region=region)),
    )
    res = select_region(None)
    assert res == region

    captured = capsys.readouterr()
    assert 'Error: invalid choice: does-not-exist' in captured.out


def test_select_region_prev_config(capsys):
    region = 'us-east-1'
    prev_config = EC2Config(None, None, region, None, None, None, None, None)
    assert select_region(prev_config) == region
    captured = capsys.readouterr()
    assert 'Found existing region, continuing with {region}'.format(region=region) in captured.out


@mock_ec2
def test_get_validated_ami_id(monkeypatch, capsys):
    client = boto3.client('ec2', region_name='us-east-1')

    source_ami_id = 'ami-03cf127a'

    monkeypatch.setattr(
        'sys.stdin',
        io.StringIO('does-not-exist\n{source_ami_id}\n'.format(source_ami_id=source_ami_id)),
    )
    res = get_validated_ami_id(client)

    assert res == source_ami_id
    captured = capsys.readouterr()

    prompt = 'Choose an AMI to use (must be Debian-based) [default is ami-08fd8ae3806f09a08 (us-west-1)]:'
    assert captured.out.strip() == u'{prompt} \u274C  Specified AMI does not exist in the chosen region, fix to continue\n\n{prompt}'.format(
        prompt=prompt
    )
