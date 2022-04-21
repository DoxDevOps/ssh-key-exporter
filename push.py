#!/usr/bin/python
import json
import os
import platform
import subprocess

import requests as requests


def get_xi_data(url):
    response = requests.get(url)
    data = json.loads(response.text)
    # data = data[]['fields']
    return data


"""10.44.0.65
Username: meduser
Password: User*12345"""

site_details = get_xi_data('http://10.44.0.52/sites/api/v1/get_sites')
length = len(site_details)
counter = 0
print(f"******** NUMBER OF SITES : {length}")

while counter < length:

    # check if site is connected
    ipaddress = site_details[counter]["fields"]["ip_address"]
    username = site_details[counter]["fields"]["username"]
    name = site_details[counter]["fields"]["name"]

    param = '-n' if platform.system().lower() == 'windows' else '-c'
    print("******************")
    print(f" checking site {name} : {counter}/{length}")
    print("******************")

    if subprocess.call(['ping', param, '1', ipaddress]) == 0:
        print("##########")
        print(f"step 1 :  {name} :  REACHABLE)")
        passwords = ["letmein", "xxr_pq7", "lin1088", "password", "lin@1088", "czemr2020!", "KSCv4GQ"]
        ssh_code = 1  # some random number to check password

        for each in passwords:
            if ssh_code != 0:
                # if connected, then push ssh keys
                # answer = os.system("ssh-copy-id "+username+"@"+ipaddress+" | echo 'yes \n' ")
                answer = os.system(
                    "sshpass -p " + each + " ssh-copy-id -o StrictHostKeyChecking=no " + username + "@" + ipaddress)
            if ssh_code == 0:
                print("SSH KEY ADDED")
                ssh_code = 1
            ssh_code = answer
            # print(site_details[counter]["fields"]["ip_address"])
            print(f" Site : {name} needs a new password")
            print("########## END")
    counter += 1

"""print("starting 1")
key = open(os.path.expanduser('~/.ssh/id_rsa.pub')).read()

"""
