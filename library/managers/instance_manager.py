import sys
import os
import time
import boto3.ec2
from botocore.exceptions import ClientError

class Instance_manager(object):
    ec2 = boto3.client('ec2')

    def __init__(self) -> None:
        credentials = self.read_credentials()
        self.Mem.instance_id = credentials[0]
        print()

    class Mem:
        instance_id = ""


    def read_credentials(self):
        credentials_file_path = os.path.join(os.path.dirname(__file__), "instance_id.txt")
        try:
            with open(credentials_file_path, 'r') as f:
                credentials = [line.strip() for line in f]
                return credentials
        except FileNotFoundError as e:
            print("Error Message: {0}".format(e))

    def start_ec2(self):
        print("------------------------------")
        print("Try to start the EC2 instance.")
        print("------------------------------")

        try:
            print("Start dry run...")
            self.ec2.start_instances(InstanceIds=[self.Mem.instance_id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, run start_instances without dryrun
        try:
            print("Start instance without dry run...")
            response = self.ec2.start_instances(InstanceIds=[self.Mem.instance_id], DryRun=False)
            print(response)
            self.fetch_public_ip()
        except ClientError as e:
            print(e)


    def stop_ec2(self):
        print("------------------------------")
        print("Try to stop the EC2 instance.")
        print("------------------------------")

        try:
            self.ec2.stop_instances(InstanceIds=[self.Mem.instance_id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.stop_instances(InstanceIds=[self.Mem.instance_id], DryRun=False)
            print(response)
        except ClientError as e:
            print(e)

    ##This has not been tested
    def hibernate_ec2(self):
        print("------------------------------")
        print("Try to hibernate the EC2 instance.")
        print("------------------------------")

        try:
            self.ec2.stop_instances(InstanceIds=[self.Mem.instance_id], Hibernate=True, DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.stop_instances(InstanceIds=[self.Mem.instance_id], Hibernate=True, DryRun=False)
            print(response)
        except ClientError as e:
            print(e)


    def fetch_public_ip(self):
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