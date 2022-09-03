import os
from re import I
import time
import random
import boto3
from botocore.exceptions import ClientError, WaiterError

class Instance_manager(object):
    ec2 = boto3.client('ec2',region_name='eu-west-2')
    ssm = boto3.client('ssm',region_name='eu-west-2')
    instance_id = [""]
    active_instances = []

    def __init__(self) -> None:
        self.instance_id = self.read_credentials()
        print()

    def get_instance_id(self, index: int) -> str:
        return self.instance_id[index]
    
    def get_random_instance(self) -> int:
        i = -1
        if (self.get_total_instances > self.get_total_active):
            while i in self.active_instances or i == -1:
                i = random.randint(0, self.get_total_instances)

        return i
    
    def get_total_active(self) -> int:
        return len(self.active_instances)

    def get_total_instances(self) -> int:
        return len(self.instance_id)

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
            self.active_instances.add(index)
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
            self.active_instances.remove(index)
            print(response)
        except ClientError as e:
            print(e)

    ##This function should work in theory, but our EC2 g3 instance does not support hibernation so it is never used
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

    def send_commands(self, index: int, commands: list[str]) -> None:
        instance_id = self.get_instance_id(index)
        
        print("Sending commands:")
        for cmd in commands:
            print(cmd)
        print("To server " + str(index))

        response = self.ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands': commands
            }
        )
        time.sleep(2)

        command_id = response['Command']['CommandId']

        waiter = self.ssm.get_waiter("command_executed")
        try:
            waiter.wait(
                CommandId=command_id,
                InstanceId=instance_id,
            )
        except WaiterError as ex:
            print(ex)
            return

        output = self.ssm.get_command_invocation( CommandId=command_id, InstanceId=instance_id)
        
        print("Output: " + output['StandardOutputContent'])