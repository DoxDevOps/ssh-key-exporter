#!/usr/bin/python
import json
import os
import platform
import subprocess
import requests as requests
from config.config import data
import pandas as pd

_PASSWORDS_ = data["PASSWORD"]
_ENDPOINT_ = data["ENDPOINT"]
print(_ENDPOINT_)
_pushed_report_excel_ = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
_not_pushed_report_excel_ = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])


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
    connection_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    unreachable_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    pushed_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    not_pushed_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])

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
            print("*************")
            print("step 1 :  " + name + ": is REACHABLE")
            connection_report_excel = connection_report_excel.append(
                {'ip': ipaddress, 'facility': name, 'username': username, 'code': 0}, ignore_index=True)
            connection_report_excel.to_excel('Reachable-Report.xlsx', index=False, header=True)

        _counter_ += 1
        unreachable_report_excel = unreachable_report_excel.append(
            {'ip': ipaddress, 'facility': name, 'username': username, 'code': 1}, ignore_index=True)
        unreachable_report_excel.to_excel('unreachable_report_excel.xlsx', index=False, header=True)

        _counter_ += 1
        unreachable_report_excel = unreachable_report_excel.append(
            {'ip': ipaddress, 'facility': name, 'username': username, 'code': 1}, ignore_index=True)
        unreachable_report_excel.to_excel('unreachable_report_excel.xlsx', index=False, header=True)
    return 1


def push_ssh_keys():
    # then try to push ssh keys
    # then try to push ssh keys
    ip_address = sites_from_xi[_counter_]["fields"]["ip_address"]
    username = sites_from_xi[_counter_]["fields"]["username"]
    facility = sites_from_xi[_counter_]["fields"]["name"]

    ssh_code_occurrences = []
    # 1 define files to keep pushed ssh sites

    print("Starting to push SSH KEYS at : " + facility)

    for each_password in _PASSWORDS_:
        # if connected, then push ssh keys
        # answer = os.system("ssh-copy-id "+username+"@"+ipaddress+" | echo 'yes \n' ")
        ssh_code = os.system(
            "sshpass -p " + each_password + " ssh-copy-id -o StrictHostKeyChecking=no " + username + "@" + ip_address)
        # os.system(
        # "ssh meduser@10.44.0.65 | echo 'User*12345' && sshpass -p " + each + " ssh-copy-id -o StrictHostKeyChecking=no " + username + "@" + ipaddress)

        ssh_code_occurrences.append(ssh_code)
        print("all ssh key push test are as follows :")
        print(ssh_code_occurrences)
        print("-----DONE-----")
    if 0 in ssh_code_occurrences:
        print("SSH KEY ADDED")
        pushed_report_excel = pushed_report_excel.append(
            {'ip': ip_address, 'facility': facility, 'username': username, 'code': ssh_code}, ignore_index=True)

        # print("Returned code : " + ssh_code + "")
    else:
        not_pushed_report_excel = not_pushed_report_excel.append(
            {'ip': ip_address, 'facility': facility, 'username': username, 'code': ssh_code}, ignore_index=True)

    not_pushed_report_excel.to_excel('not_pushed_report_excel.xlsx', index=False, header=True)
    pushed_report_excel.to_excel('pushed_report_excel.xlsx', index=False, header=True)

    print("*****************************************************************************************")

    return 1


# ************************** RUN THE SCRIPT **************************************************

site_details = get_xi_data(_ENDPOINT_)
check_connectivity(site_details)
