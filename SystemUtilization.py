from curses import echo
import re
from fabric import Connection
import paramiko


def get_host_system_details(user_name: str, ip_address: str) -> str:
    """gets version of operating system running on remote host
       gets storage stats of remote host
       gets ram stats of remote host

    Args:
        user_name (str): remote user name
        ip_address (str): ip address of remote server

    Returns:
        list: [os_name,
               os_version,
               cpu_utilization,
               hdd_total_storage,
               hdd_remaing_storage,
               hdd_used_storage,
               hdd_remaing_in_percentiles,
               total_ram,
               used_ram,
               remaining_ram
            ]
    """
    try:

        ssh = paramiko.SSHClient()
        # ssh.load_host_keys('/home/username/.ssh/known_hosts')
        # ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # Establish a connection with a hard coded pasword
        # a private key will be used soon
        #                                           AUTO SSH IS NEEDED ON THIS
        ssh.connect(ip_address, username=user_name, password='123456')
        # Linux command for system version inf
        stdin, stdout, stderr = ssh.exec_command("cat /etc/os-release")
        # Output command execution results
        result = stdout.read().splitlines()
        # string of both os name and version
        inputstring = f"{result[0]} {result[1]}"
        # array of both os anme and version
        collection = re.findall('"([^"]*)"', inputstring)

        # Linux command for cpu utilazation command
        get_cpu_uti_cmd = "top -bn2 | grep '%Cpu' | tail -1 | grep -P '(....|...) id,'|awk '{print  100-$8 }'"
        # executing command for writing to stdout
        stdin, stdout, stderr = ssh.exec_command(get_cpu_uti_cmd)
        # getting value for cpu utilzation
        cpu_utilization = stdout.read().splitlines()[0]
        cpu_utilization = f"{cpu_utilization}"
        collection.append(cpu_utilization.split("'")[1])

        # Linux command for HDD utilazation command
        get_hdd_uti_cmd = "df -h -t ext4"
        # executing command for writing to stdout
        stdin, stdout, stderr = ssh.exec_command(get_hdd_uti_cmd)
        # getting values for hdd utilaztion
        hdd_utilazation = stdout.read().splitlines()[1]
        hdd_utilazation = f"{hdd_utilazation}".split()
        # total_storage
        collection.append(hdd_utilazation[1])
        # remaining_storage
        collection.append(hdd_utilazation[2])
        # used_storage
        collection.append(hdd_utilazation[3])
        # remaining_storage_percentile
        collection.append(hdd_utilazation[4])

        # Linux command for RAM utilazation command
        get_ram_uti_cmd = "free -h"
        # executing command for writing to stdout
        stdin, stdout, stderr = ssh.exec_command(get_ram_uti_cmd)
        # getting values for hdd utilaztion
        ram_utilazation = stdout.read().splitlines()[1]
        ram_utilazation = f"{ram_utilazation}".split()
        # total_ram
        collection.append(ram_utilazation[1])
        # used_ram
        collection.append(ram_utilazation[2])
        # remaining_ram
        collection.append(ram_utilazation[6])

        # Close the connection
        ssh.close()

    except Exception as e:
        print(
            f"--- Failed to get host system details for {ip_address} with exception: {e} ---")
        return "failed_to_get_host_system_details"

    return collection
