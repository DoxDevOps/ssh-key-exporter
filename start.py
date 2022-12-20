#!/usr/bin/python
import json
import os
import platform
import subprocess
import time

import distro as distro
from fabric import Connection
import requests as requests
from invoke import Exit
import paramiko

from SystemUtilization import get_host_system_details
from config.config import data
import pandas as pd

_PASSWORDS_ = data["PASSWORD"]
_ENDPOINT_ = data["ENDPOINT"]


def get_xi_data(url):
    """
    function that gets all sites from xi
    :param url: endpoint
    :return: json object containing site details
    """
    response = requests.get(url)
    site_data = json.loads(response.text)
    return site_data


def check_connectivity(sites_from_xi):
    _counter_ = 0  # this is a checker
    number_of_sites = len(sites_from_xi)
    _connection_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    _unreachable_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])

    while _counter_ < number_of_sites:
        print("******************** PROGRESS BAR ******************************")
        print("Checking site number {} out of {} : ".format(_counter_ + 1, number_of_sites))
        print("**************************************************")

        ipaddress = sites_from_xi[_counter_]["fields"]["ip_address"]  # get the IP address
        username = sites_from_xi[_counter_]["fields"]["username"]  # get the username
        name = sites_from_xi[_counter_]["fields"]["name"]  # get the site name

        # 4. Check if a site is reachable
        param = '-n' if platform.system().lower() == 'windows' else '-c'

        if subprocess.call(['ping', param, '1', ipaddress]) == 0:
            print("*********************************** REACHABLE***********************************")
            print("step 1 :  " + name + ": is REACHABLE")
            _connection_report_excel = _connection_report_excel.append(
                {'ip': ipaddress, 'facility': name, 'username': username, 'code': 0}, ignore_index=True)

        else:
            print("*********************************** REACHABLE***********************************")
            print("step 1 :  " + name + ": is NOT REACHABLE")
            _unreachable_report_excel = _unreachable_report_excel.append(
                {'ip': ipaddress, 'facility': name, 'username': username, 'code': 1}, ignore_index=True)

        _counter_ += 1
    _connection_report_excel.to_excel('Reachable-Report.xlsx', index=False, header=True)
    _unreachable_report_excel.to_excel('unreachable_report_excel.xlsx', index=False, header=True)

    return 1


def auto_log_in():
    # 1. Open Excel file with pushed ssh sites
    # 2. check if the site can be auto ssh(ed)
    # 3. get the uname to confirm. the uname must be Linux since all servers are Linux
    _auto_ssh_report_ = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    _cannot_auto_ssh_report_ = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])

    all_pushed_reachable_sites = pd.read_excel('./pushed-report_excel.xlsx')
    for each_ip_address in all_pushed_reachable_sites['ip'].values:
        facility = (
            all_pushed_reachable_sites.loc[(all_pushed_reachable_sites['ip'] == each_ip_address, 'facility')].item())
        username = (
            all_pushed_reachable_sites.loc[(all_pushed_reachable_sites['ip'] == each_ip_address, 'username')].item())

        result = Connection('meduser@10.41.0.2').run('uname -s')
        if 'Linux' == result.stdout:
            _auto_ssh_report_ = _auto_ssh_report_.append(
                {'ip': each_ip_address, 'facility': facility, 'username': username, 'code': 0}, ignore_index=True)
        else:
            # cannot auto ssh although a key was pushed
            _cannot_auto_ssh_report_ = _cannot_auto_ssh_report_.append(
                {'ip': each_ip_address, 'facility': facility, 'username': username, 'code': 0}, ignore_index=True)
        raise Exit("Sorry Bridge could auto ssh into ABC site")
    _auto_ssh_report_.to_excel('auto_ssh_sites.xlsx', index=False, header=True)
    _cannot_auto_ssh_report_.to_excel('cannot_auto_ssh_sites.xlsx', index=False, header=True)

    return 1


def push_ssh_keys():
    # Step 1 : get the parameters for sites  that are connected
    print("##################################### PUSHING SSH KEYS "
          "###############################################################################")
    all_reachable_sites = pd.read_excel('./Reachable-Report.xlsx')
    # Step 2 : try to push ssh keys using the password provided.
    _pushed_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    _not_pushed_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    ssh_code_occurrences = []
    # Step 3: Loop through the connected sites define files to keep pushed ssh sites
    for each in all_reachable_sites['ip'].values:
        facility = (all_reachable_sites.loc[(all_reachable_sites['ip'] == each, 'facility')].item())
        username = (all_reachable_sites.loc[(all_reachable_sites['ip'] == each, 'username')].item())

        for each_password in _PASSWORDS_:
            # if connected, then push ssh keys
            # answer = os.system("ssh-copy-id "+username+"@"+ipaddress+" | echo 'yes \n' ")
            ssh_code = os.system(
                "sshpass -p " + each_password + " ssh-copy-id -o StrictHostKeyChecking=no " + all_reachable_sites.loc[
                    (all_reachable_sites['ip'] == each, 'username')].item() + "@" + each)

            ssh_code_occurrences.append(ssh_code)
        print(f"All ssh key push test are as follows : {ssh_code_occurrences} and this is for {facility}")

        print("-----DONE-----")

        if 0 in ssh_code_occurrences:
            print(f"********** SUCCESS : Key pushed to {facility}  **********")
            _pushed_report_excel = _pushed_report_excel.append(
                {'ip': each, 'facility': facility, 'username': username, 'code': 0}, ignore_index=True)

            # print("Returned code : " + ssh_code + "")
        else:
            print(f"********** FAILURE : Key NOT pushed to {facility}  **********")
            _not_pushed_report_excel = _not_pushed_report_excel.append(
                {'ip': each, 'facility': facility, 'username': username, 'code': ssh_code_occurrences},
                ignore_index=True)

        _not_pushed_report_excel.to_excel('not_pushed_report_excel.xlsx', index=False, header=True)
        _pushed_report_excel.to_excel('pushed_report_excel.xlsx', index=False, header=True)

        del ssh_code_occurrences[:]  # delete the list

    return 1


def get_emr_version():
    directory = {"HIS-Core": "/var/www/HIS-Core", "BHT-EMR-API": "/var/www/BHT-EMR-API"}
    all_pushed_ssh_sites = pd.read_excel('./auto_ssh_sites.xlsx')

    port = 22
    version_dict = {}
    for each_ip in all_pushed_ssh_sites['ip'].values:
        # facility = (all_pushed_ssh_sites.loc[(all_pushed_ssh_sites['ip'] == each, 'facility')].item())
        username = (all_pushed_ssh_sites.loc[(all_pushed_ssh_sites['ip'] == each_ip, 'username')].item())

        for each_directory in directory:
            command = "/usr/bin/git  --git-dir={}/.git describe --tags `git rev-list --tags --max-count=1` \n".format(
                directory)

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(each_ip, port, username)

            stdin, stdout, stderr = ssh.exec_command(command)

            tag = stdout.readlines()
            stdin.close()
            version_dict[each_directory] = str(tag, 'utf-8')
        json_object = json.dumps(version_dict)
        json_object = json.loads(json_object)
        print(json_object)
    return 1


def get_system_utilization():
    print("get all stats")
    details = get_host_system_details("meduser", "10.41.0.2")
    # print(details)
    # calculating hdd_used_in_percentiles
    hdd_used_in_percentiles = (int(''.join(filter(str.isdigit, details[5]))) /
                               int(''.join(filter(str.isdigit, details[3])))) * 100
    hdd_used_in_percentiles = round(hdd_used_in_percentiles)
    host_details = {"ip_address": "10.41.0.2",
                    "os_name": details[0],
                    "os_version": details[1],
                    "cpu_utilization": details[2],
                    "hdd_total_storage": details[3],
                    "hdd_remaining_storage": details[4],
                    "hdd_used_storage": details[5],
                    "hdd_used_in_percentile": f"{hdd_used_in_percentiles}%",
                    "total_ram": details[7],
                    "used_ram": details[8],
                    "remaining_ram": details[9]
                    }

    print(host_details)

    return details


# ************************** RUN THE SCRIPT **************************************************

# site_details = get_xi_data(_ENDPOINT_)
# check_connectivity(site_details)
# push_ssh_keys()
# get_emr_version()
# auto_log_in()
get_system_utilization()
