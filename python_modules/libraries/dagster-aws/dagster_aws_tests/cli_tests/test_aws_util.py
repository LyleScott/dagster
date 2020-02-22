import boto3
from dagster_aws.cli.aws_util import (
    VPC_CREATION_WARNING,
    create_security_group,
    get_validated_ami_id,
    select_region,
    select_vpc,
)
from dagster_aws.cli.config import EC2Config
from moto import mock_ec2
from six import StringIO


@mock_ec2
def test_select_region(monkeypatch, capsys):
    region = 'us-east-1'
    monkeypatch.setattr(
        'sys.stdin', StringIO('does-not-exist\n{region}\n'.format(region=region)),
    )
    res = select_region(None)
    assert res == region

    captured = capsys.readouterr()
    assert 'Error: invalid choice: does-not-exist' in captured.out


@mock_ec2
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
        StringIO('does-not-exist\n{source_ami_id}\n'.format(source_ami_id=source_ami_id)),
    )
    res = get_validated_ami_id(client)

    assert res == source_ami_id
    captured = capsys.readouterr()

    prompt = 'Choose an AMI to use (must be Debian-based) [default is ami-08fd8ae3806f09a08 (us-west-1)]:'
    assert captured.out.strip() == u'{prompt} \u274C  Specified AMI does not exist in the chosen region, fix to continue\n\n{prompt}'.format(
        prompt=prompt
    )


@mock_ec2
def test_select_vpc(monkeypatch, capsys):
    client = boto3.client('ec2', region_name='us-east-1')
    ec2 = boto3.resource('ec2', region_name='us-east-1')

    filters = [{'Name': 'isDefault', 'Values': ['true']}]
    default_vpc = list(ec2.vpcs.filter(Filters=filters))[0].id  # pylint: disable=no-member
    monkeypatch.setattr(
        'sys.stdin', StringIO('does-not-exist\n{default_vpc}\n'.format(default_vpc=default_vpc)),
    )
    vpc = select_vpc(client, ec2)

    captured = capsys.readouterr()

    assert vpc == default_vpc
    assert VPC_CREATION_WARNING in captured.out
    assert 'Select an existing VPC ID to use' in captured.out
    assert 'Specified VPC does-not-exist does not exist' in captured.out


@mock_ec2
def test_select_vpc_created(monkeypatch):
    client = boto3.client('ec2', region_name='us-east-1')
    ec2 = boto3.resource('ec2', region_name='us-east-1')

    vpc = ec2.create_vpc(CidrBlock='172.16.0.0/16')  # pylint: disable=no-member
    monkeypatch.setattr(
        'sys.stdin', StringIO('{vpc_id}\n'.format(vpc_id=vpc.id)),
    )
    selected_vpc = select_vpc(client, ec2)
    assert vpc.id == selected_vpc


@mock_ec2
def test_create_security_groups(monkeypatch, capsys):
    client = boto3.client('ec2', region_name='us-east-1')
    ec2 = boto3.resource('ec2', region_name='us-east-1')

    filters = [{'Name': 'isDefault', 'Values': ['true']}]
    default_vpc = list(ec2.vpcs.filter(Filters=filters))[0].id  # pylint: disable=no-member

    print(
        "client.describe_security_groups()['SecurityGroups']",
        client.describe_security_groups()['SecurityGroups'],
    )

    monkeypatch.setattr(
        'sys.stdin', StringIO('default\nmynewcoolgroup\n'),
    )
    prev_config = None
    res = create_security_group(prev_config, client, ec2, default_vpc)

    filters = [{'Name': 'isDefault', 'Values': ['true']}]
    sg_described = client.describe_security_groups(GroupIds=[res])['SecurityGroups'][0]

    assert sg_described['Description'] == 'dagit Security Group'
    assert sg_described['GroupName'] == 'mynewcoolgroup'

    assert sg_described['IpPermissions'] == [
        {
            'FromPort': 3000,
            'IpProtocol': 'tcp',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
            'ToPort': 3000,
            'UserIdGroupPairs': [],
        },
        {
            'FromPort': 22,
            'IpProtocol': 'tcp',
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}],
            'ToPort': 22,
            'UserIdGroupPairs': [],
        },
    ]
    assert sg_described['Tags'] == [{'Key': 'Name', 'Value': 'mynewcoolgroup'}]

    next_group = 'myothercoolgroup'
    prev_config = EC2Config(None, None, None, next_group, None, None, None, None)
    assert create_security_group(prev_config, client, ec2, default_vpc) == next_group
    captured = capsys.readouterr()
    assert (
        'Found existing security group, continuing with {group}'.format(group=next_group)
        in captured.out
    )
