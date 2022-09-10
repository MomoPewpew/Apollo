import asyncio
import os
from re import I
import shutil
import time
import random
import boto3
from botocore.exceptions import ClientError, WaiterError

class Instance_manager(object):
    ec2 = boto3.client('ec2',region_name='eu-west-2')
    ssm = boto3.client('ssm',region_name='eu-west-2')
    instance_ips = []
    instance_statuses = []

    def __init__(self) -> None:
        self.instance_ids = self.read_credentials()
        for append in range(len(self.instance_ids) + 1):
            self.instance_ips.append("")
            self.instance_statuses.append("stopped")

        print()

    def read_credentials(self) -> list[str]:
        credentials_file_path = os.path.join(os.path.dirname(__file__), "instance_ids.txt")
        try:
            with open(credentials_file_path, 'r') as f:
                credentials = [line.strip() for line in f]
                return credentials
        except FileNotFoundError as e:
            print("Error Message: {0}".format(e))

    def get_instance_id(self, index: int) -> str:
        return self.instance_ids[index]

    def get_instance_ip(self, index: int) -> str:
        return self.instance_ips[index]

    def get_instance_index(self, id: str) -> int:
        return self.instance_ids.index(id)
    
    def is_instance_listed(self, id: str) -> bool:
        return id in self.instance_ids
    
    def get_random_instance(self) -> int:
        i = -1
        if (self.can_boot()):
            most_favorable_status = "stopping"
            if self.should_boot(): most_favorable_status = "stopped"

            while i == -1 or self.fetch_ec2_statuses[i] != most_favorable_status:
                i = random.randint(0, len(self.instance_ids) - 1)

        return i
    
    async def force_status_update_all(self) -> None:
        for index in range(len(self.instance_statuses)):
            await self.force_status_update(index)

    async def force_status_update(self, index: int) -> None:
        self.instance_statuses[index] = await self.fetch_ec2_status(index)
        if self.instance_statuses[index] == "running" and await self.is_ssm_available(index):
            self.instance_statuses[index] = "available"

    ##can_boot checks whether it's possible to boot an instance
    def can_boot(self) -> None:
        return (
            "stopped" in self.instance_statuses or
            "stopping" in self.instance_statuses
        )
    
    ##should_boot checks whether booting something would be faster to boot an instance than to wait for active instances to finish
    def should_boot(self) -> None:
        return (
            "stopped" in self.instance_statuses
        )
    
    ##must_boot checks whether booting up a new instance is a neccesity
    def must_boot(self) -> None:
        return not (
            "pending" in self.instance_statuses or
            "running" in self.instance_statuses or
            "available" in self.instance_statuses or
            "busy" in self.instance_statuses
        )

    async def start_ec2(self, index: int) -> None:
        self.instance_statuses[index] = await self.fetch_ec2_status(index)

        if self.instance_statuses[index] == "stopped" or self.instance_statuses[index] == "stopping":
            if self.instance_statuses[index] == "stopping":
                print(f"Tried to start instance {index} but it was stopping. The process will automatically be resumed after a complete stop.")
                while await self.fetch_ec2_status(index) != "stopped":
                    await asyncio.sleep(30)

            print(f"Trying to start instance {index}")

            try:
                print("  Start dry run...")
                self.ec2.start_instances(InstanceIds=[self.get_instance_id(index)], DryRun=True)
            except ClientError as e:
                if 'DryRunOperation' not in str(e):
                    raise

            # Dry run succeeded, run start_instances without dryrun
            try:
                print("  Start instance without dry run...")
                self.instance_statuses[index] = "pending"
                self.ec2.start_instances(InstanceIds=[self.get_instance_id(index)], DryRun=False)
                await asyncio.sleep(30)
            except ClientError as e:
                print(e)
        else:
            print(f"Tried to start instance {index} but it was already running. Attempting to engage it anyway.")

        await self.fetch_public_ip(index)
        self.instance_statuses[index] = "running"

        while not await self.is_ssm_available(index):
            await asyncio.sleep(2)
        self.instance_statuses[index] = "available"
        print(f"  Instance {index} is now available.")

    def stop_ec2(self, index: int) -> None:
        print(f"Trying to stop instance {index}")

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

    ##This function should work in theory, but our EC2 g3 instance does not support hibernation so it is never used
    def hibernate_ec2(self, index: int) -> None:
        print(f"Trying to hibernate instance {index}")

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

    async def fetch_public_ip(self, index: int) -> None:
        instances = self.ec2.describe_instances()["Reservations"][0]["Instances"]

        instance_ids = []
        ip_addresses = []

        for instance in instances:
            instance_ids.append(instance["InstanceId"])
            ip_addresses.append(format(instance["PublicIpAddress"]))

        self.instance_ips[index] = ip_addresses[instance_ids.index(self.get_instance_id(index))]

        print(f"  Public IPv4 address of the EC2 instance: {self.instance_ips[index]}")

    async def fetch_ec2_status(self, index: int) -> str:
        instances = self.ec2.describe_instances()["Reservations"][0]["Instances"]
        instance_ids = []
        states = []

        for instance in instances:
            instance_ids.append(instance["InstanceId"])
            states.append(instance["State"]["Name"])

        instance_id = self.get_instance_id(index)

        if instance_id in instance_ids:
            return states[instance_ids.index(instance_id)]
        else:
            return "unknown"

    async def is_ssm_available(self, index: int) -> bool:
        ssm_ids = []

        for instance_information in self.ssm.describe_instance_information()["InstanceInformationList"]:
            ssm_ids.append(instance_information["InstanceId"])

        return (self.get_instance_id(index) in ssm_ids)

    async def send_command(self, index: int, command: str) -> None:
        await self.send_commands(index, [command])

    async def send_commands(self, index: int, commands: list[str]) -> None:
        instance_id = self.get_instance_id(index)
        
        print("Sending commands:")
        for cmd in commands:
            print(cmd)
        print(f"To instance {index}")

        response = self.ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands': commands
            }
        )
        await asyncio.sleep(2)

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
        
        print(output['StandardOutputContent'])

    def download_output(self, index: int) -> None:
        path = os.path.join("./out/", f"instance_{index}")

        if not os.path.exists(path):
            os.mkdir(path)

        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

        os.system(f"scp -o \"StrictHostKeyChecking no\" -i daedaluspem.pem ubuntu@{self.get_instance_ip(index)}:/home/ubuntu/Daedalus/out/* ./out/instance_{index}")