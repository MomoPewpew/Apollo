import asyncio
import os
import shutil
import random
from typing import Union
import boto3
from botocore.exceptions import ClientError
from ..db import db
from .. import bot

class Instance_manager(object):
    ec2 = boto3.client('ec2',region_name='eu-west-2')
    ssm = boto3.client('ssm',region_name='eu-west-2')
    instance_ips = []
    instance_statuses = []

    def __init__(self, bot: bot) -> None:
        self.bot = bot
        self.instance_ids = self.read_credentials()
        for append in range(self.get_total_instances()):
            self.instance_ips.append("")
            self.instance_statuses.append("stopped")

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
    
    def is_instance_booting(self, index: str) -> bool:
        return (self.instance_statuses[index] == "pending" or self.instance_statuses[index] == "running")

    def get_total_instances(self) -> int:
        return len(self.instance_ids)
    
    def get_total_active(self) -> int:        
        return self.instance_statuses.count("pending", "running", "available", "busy")
    
    def get_active_list(self) -> list[int]:
        returnList = []

        for i in range(len(self.instance_statuses)):
            status = self.instance_statuses[i]
            if (status == "pending" or
                status == "running" or
                status == "available" or
                status == "busy"
            ):
                returnList.append(i)
        
        return returnList

    def get_random_instance(self) -> int:
        i = -1
        if (self.can_boot()):
            most_favorable_status = "stopping"
            if self.should_boot(): most_favorable_status = "stopped"

            while i == -1 or self.instance_statuses[i] != most_favorable_status:
                i = random.randint(0, self.get_total_instances() - 1)

        return i
    
    def get_available_instance(self) -> int:
        if "available" in self.instance_statuses:
            for i in range(len(self.instance_statuses)):
                if self.instance_statuses[i] == "available":
                    return i
        else:
            return -1
    
    async def get_most_available_instance(self) -> Union[int, bool]:
        most_favorable_status = "stopping"
        if "available" in self.instance_statuses: most_favorable_status = "available"
        elif "running" in self.instance_statuses: most_favorable_status = "running"
        elif "pending" in self.instance_statuses: most_favorable_status = "pending"
        elif "stopped" in self.instance_statuses: most_favorable_status = "stopped"

        if most_favorable_status == "running" or most_favorable_status == "pending":
            while "available" not in self.instance_statuses:
                if "running" in self.instance_statuses or "pending" in self.instance_statuses:
                    asyncio.sleep(2)
                    self.update_instance_statuses()
                else:
                    return -1, False

            most_favorable_status = "available"

        for i in range(len(self.instance_statuses)):
            if self.instance_statuses[i] == most_favorable_status:
                return i, most_favorable_status != "available"
    
    def all_instances_stopping(self) -> bool:
        return ((self.instance_statuses.count("stopping") + self.instance_statuses.count("stoppingthenstarting")) >= len(self.instance_statuses))

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
            "stoppingthenstarting" in self.instance_statuses or
            "pending" in self.instance_statuses or
            "running" in self.instance_statuses or
            "available" in self.instance_statuses or
            "busy" in self.instance_statuses
        )

    async def start_ec2(self, index: int) -> None:
        await self.update_instance_statuses()

        if self.instance_statuses[index] == "stopped" or self.instance_statuses[index] == "stopping":
            if self.instance_statuses[index] == "stopping":
                self.instance_statuses[index] = "stoppingthenstarting"
                print(f"Tried to start instance {index} but it was stopping. The process will automatically be resumed after a complete stop.")
                while "stopping" in self.instance_statuses[index]:
                    await asyncio.sleep(30)
                    await self.update_instance_statuses()

                    taskIDs = db.column("SELECT taskID FROM tasks WHERE timeSent is NULL")
                    if len(taskIDs) < 1:
                        self.instance_statuses[index] = "stopping"
                        return

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
            self.instance_statuses[index] = "stopping"
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
            self.instance_statuses[index] = "stopping"
            response = self.ec2.stop_instances(InstanceIds=[self.get_instance_id(index)], Hibernate=True, DryRun=False)
            print(response)
        except ClientError as e:
            print(e)

    async def update_instance_statuses(self) -> str:
        instance_ids = []
        states = []
        ip_addresses = []

        for instance in self.ec2.describe_instances()["Reservations"][0]["Instances"]:
            instance_ids.append(instance["InstanceId"])
            states.append(instance["State"]["Name"])

            if "PublicIpAddress" in instance:
                ip_addresses.append(format(instance["PublicIpAddress"]))
            else:
                ip_addresses.append("")

        for i in range(self.get_total_instances()):
            instance_id = instance_ids[i]
            if self.is_instance_listed(instance_id):
                index = self.get_instance_index(instance_id)
                state = states[i]
                self.instance_ips[index] = ip_addresses[i]
                if not ((state == "running" and (self.instance_statuses[index] == "available" or self.instance_statuses[index] == "busy")) or (state == "stopping" and self.instance_statuses[index] == "stoppingthenstarting")):
                    self.instance_statuses[index] = state

        if "running" in self.instance_statuses:
            ssm_ids = []

            for instance_information in self.ssm.describe_instance_information()["InstanceInformationList"]:
                ssm_ids.append(instance_information["InstanceId"])
            
            for instance_id in ssm_ids:
                if self.is_instance_listed(instance_id):
                    index = self.get_instance_index(instance_id)
                    if self.instance_statuses[index] == "running":
                        self.instance_statuses[index] = "available"

    async def fetch_public_ip(self, index: int) -> None:
        instance_ids = []
        ip_addresses = []

        for instance in self.ec2.describe_instances()["Reservations"][0]["Instances"]:
            if "PublicIpAddress" in instance:
                instance_ids.append(instance["InstanceId"])
                ip_addresses.append(format(instance["PublicIpAddress"]))

        if self.get_instance_id(index) in instance_ids:
            self.instance_ips[index] = ip_addresses[instance_ids.index(self.get_instance_id(index))]

            print(f"  Public IPv4 address of instance {index}: {self.instance_ips[index]}")

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

        output = self.ssm.get_command_invocation( CommandId=command_id, InstanceId=instance_id)
        while output["Status"] == "InProgress":
            output = self.ssm.get_command_invocation( CommandId=command_id, InstanceId=instance_id)
            await asyncio.sleep(1)

        print(output['StandardOutputContent'])

    async def download_output(self, index: int) -> None:
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

        os.system(f"scp -o \"StrictHostKeyChecking no\" -i daedaluspem.pem ubuntu@{self.get_instance_ip(index)}:{self.bot.daedalusBasePath}/out/* ./out/instance_{index}")