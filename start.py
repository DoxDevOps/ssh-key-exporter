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


def get_xi_data(url):
    """
    function that gets all sites from xi
    :param url: endpoint
    :return: json object containing site details
    """
    response = requests.get(url)
    site_data = json.loads(response.text)
    print(site_data)
    return site_data


def check_connectivity(sites_from_xi):
    _counter_ = 0  # this is a checker
    number_of_sites = len(sites_from_xi)
    _connection_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    _unreachable_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])

    while _counter_ < 50:
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


            # then try to push ssh Keys ( ONLY FOR SITES THAT ARE REACHABLE)
            push_ssh_keys(ipaddress, username, name)

        else:
            print("*********************************** REACHABLE***********************************")
            print("step 1 :  " + name + ": is NOT REACHABLE")
            _unreachable_report_excel = _unreachable_report_excel.append(
                {'ip': ipaddress, 'facility': name, 'username': username, 'code': 1}, ignore_index=True)

        _counter_ += 1
    _connection_report_excel.to_excel('Reachable-Report.xlsx', index=False, header=True)
    _unreachable_report_excel.to_excel('unreachable_report_excel.xlsx', index=False, header=True)

    return 1


def push_ssh_keys(ip_address, username, facility):

    # Step 1 : get the parameters for sites  that are connected
    all_reachable_sites = pd.read_excel('./Reachable-Report.xlsx')
    # Step 2 : try to push ssh keys using the password provided.
    _pushed_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    _not_pushed_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'code'])
    ssh_code_occurrences = []
    # Step 3: Loop through the connected sites define files to keep pushed ssh sites
    for each in all_reachable_sites['ip'].values:
        for each_password in _PASSWORDS_:
            # if connected, then push ssh keys
            # answer = os.system("ssh-copy-id "+username+"@"+ipaddress+" | echo 'yes \n' ")
            ssh_code = os.system(
                "sshpass -p " + each_password + " ssh-copy-id -o StrictHostKeyChecking=no " + all_reachable_sites.loc[
                    (all_reachable_sites['ip'] == each, 'username')].item() + "@" + each)

            ssh_code_occurrences.append(ssh_code)
            print("all ssh key push test are as follows :")
            print(ssh_code_occurrences)
            print("-----DONE-----")
        if 0 in ssh_code_occurrences:
            print("SSH KEY ADDED")
            facility = (all_reachable_sites.loc[(all_reachable_sites['ip'] == each, 'facility')].item())
            username = (all_reachable_sites.loc[(all_reachable_sites['ip'] == each, 'username')].item())

            _pushed_report_excel = _pushed_report_excel.append(
                {'ip': ip_address, 'facility': facility, 'username': username, 'code': ssh_code}, ignore_index=True)

            # print("Returned code : " + ssh_code + "")
        else:
            _not_pushed_report_excel = _not_pushed_report_excel.append(
                {'ip': ip_address, 'facility': facility, 'username': username, 'code': ssh_code}, ignore_index=True)

        _not_pushed_report_excel.to_excel('not_pushed_report_excel.xlsx', index=False, header=True)
        _pushed_report_excel.to_excel('pushed_report_excel.xlsx', index=False, header=True)

        print("*****************************************************************************************")

    return 1


# ************************** RUN THE SCRIPT **************************************************

site_details = get_xi_data(_ENDPOINT_)
check_connectivity(site_details)
