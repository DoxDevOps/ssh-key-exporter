#!/usr/bin/python
import json
import os
import platform
import subprocess
import requests as requests
from dotenv import load_dotenv

load_dotenv()  # load .env file
_PASSWORDS_ = os.environ.get("PASSWORD")
_ENDPOINT_ = os.environ.get("ENDPOINT")


def get_xi_data(url):
    """
    function that gets all sites from xi
    :param url: endpoint
    :return: json object containing site details
    """
    response = requests.get(url)
    site_data = json.loads(response.text)
    return site_data


# Follow the following steps :
# 1. get data from xi
site_details = get_xi_data()
# 2. record the length of the file
length = len(site_details)
counter = 0  # this is a checker
checker = True
print("Start Service !! ")
print(f"******** NUMBER OF SITES : {length}")

# 3. Loop through the sites from xi
while counter < length:
    ipaddress = site_details[counter]["fields"]["ip_address"]
    username = site_details[counter]["fields"]["username"]
    name = site_details[counter]["fields"]["name"]

    # 4. Check if a site is reachable
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    print("******************")
    print(f" checking site {name} : {counter}/{length}")
    print("******************")

    if subprocess.call(['ping', param, '1', ipaddress]) == 0:
        print("*************")
        print(f"step 1 :  {name} :  is REACHABLE)")
        passwords = ["letmein", "xxr_pq7", "lin1088", "password",
                     "lin@1088", "czemr2020!", "KSCv4GQ", "Tm3zbk4"]
        # 5. Test passwords
        for each in passwords:
            if checker:
                # if connected, then push ssh keys
                # answer = os.system("ssh-copy-id "+username+"@"+ipaddress+" | echo 'yes \n' ")
                answer = os.system(
                    "sshpass -p " + each + " ssh-copy-id -o StrictHostKeyChecking=no " + username + "@" + ipaddress)
                ssh_code = answer
                if ssh_code == 0:
                    print("SSH KEY ADDED")
                    with open("pushed.json", "r+") as data:
                        information = {f"site_name{name}": name}
                        data.write(json.dumps(information))
                        data.close()
                    checker = False
                print(f"Returned code : {ssh_code}")
        checker = True  # put it ack to default settings

        print("****************************")
    counter += 1
