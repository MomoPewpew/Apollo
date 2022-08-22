import sys
import os
import time
import boto3.ec2
from botocore.exceptions import ClientError

class Instance_manager(object):
    ec2 = boto3.client('ec2')

    class Mem:
        """
        Global Class Pattern:
        Declare globals here.
        """
        instance_id = ""


    def read_credentials(self):
        """
        Read the user's credential file 'instance_id.txt'.
        This file should be located in the user's home folder.
        :return: The EC2 instance id.
        """
        home_dir = os.path.expanduser('~')
        credentials_file_path = os.path.join(home_dir, "instance_id.txt")
        try:
            with open(credentials_file_path, 'r') as f:
                credentials = [line.strip() for line in f]
                return credentials
        except FileNotFoundError as e:
            print("Error Message: {0}".format(e))

    def start_ec2(self):
        """
        This code is from Amazon's EC2 example.
        Do a dryrun first to verify permissions.
        Try to start the EC2 instance.
        """
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
        """
        This code is from Amazon's EC2 example.
        Do a dryrun first to verify permissions.
        Try to stop the EC2 instance.
        """
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


    def fetch_public_ip(self):
        """
        Fetch the public IP that has been assigned to the EC2 instance.
        :return: Print the public IP to the console.
        """
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


    def main(self):
        """
        The entry point of this program.
        """
        credentials = self.read_credentials()
        self.Mem.instance_id = credentials[0]
        print()

    if __name__ == '__main__':
        main()