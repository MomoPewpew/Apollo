from imaplib import Commands
import os
from re import I
import time
from unittest.util import strclass
import boto3.ec2
from botocore.exceptions import ClientError

class Instance_manager(object):
    ec2 = boto3.client('ec2')
    ssm = boto3.client('ssm')
    instance_id = [""]

    def __init__(self) -> None:
        self.instance_id = self.read_credentials()
        print()

    def get_instance_id(self, index: int) -> str:
        return self.instance_id[index]

    def read_credentials(self) -> list[str]:
        credentials_file_path = os.path.join(os.path.dirname(__file__), "instance_id.txt")
        try:
            with open(credentials_file_path, 'r') as f:
                credentials = [line.strip() for line in f]
                return credentials
        except FileNotFoundError as e:
            print("Error Message: {0}".format(e))

    def start_ec2(self, index: int) -> None:
        print("------------------------------")
        print("Try to start the EC2 instance.")
        print("------------------------------")

        try:
            print("Start dry run...")
            self.ec2.start_instances(InstanceIds=[self.get_instance_id(index)], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, run start_instances without dryrun
        try:
            print("Start instance without dry run...")
            response = self.ec2.start_instances(InstanceIds=[self.get_instance_id(index)], DryRun=False)
            print(response)
            self.fetch_public_ip()
        except ClientError as e:
            print(e)

    def stop_ec2(self, index: int) -> None:
        print("------------------------------")
        print("Try to stop the EC2 instance.")
        print("------------------------------")

        try:
            self.ec2.stop_instances(InstanceIds=[self.get_instance_id(index)], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.stop_instances(InstanceIds=[self.get_instance_id(index)], DryRun=False)
            print(response)
        except ClientError as e:
            print(e)

    def hibernate_ec2(self, index: int) -> None:
        print("------------------------------")
        print("Try to hibernate the EC2 instance.")
        print("------------------------------")

        try:
            self.ec2.stop_instances(InstanceIds=[self.get_instance_id(index)], Hibernate=True, DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.stop_instances(InstanceIds=[self.get_instance_id(index)], Hibernate=True, DryRun=False)
            print(response)
        except ClientError as e:
            print(e)

    def fetch_public_ip(self) -> None:
        print()
        print("Waiting for public IPv4 address...")
        print()
        time.sleep(16)
        response = self.ec2.describe_instances()
        first_array = response["Reservations"]
        first_index = first_array[0]
        instances_dict = first_index["Instances"]
        instances_array = instances_dict[0]
        ip_address = instances_array["PublicIpAddress"]
        print()
        print("Public IPv4 address of the EC2 instance: {0}".format(ip_address))

    def send_command(self, index: int, command: str) -> str:
        commands = [command]

        resp = self.send_commands(index, commands)
        return resp

    def send_commands(self, index: int, commands: list[str]) -> str:
        instance_ids = [self.get_instance_id(index)]

        resp = self.ssm.send_command(
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': commands},
            InstanceIds=instance_ids,
        )
        return resp