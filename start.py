#!/usr/bin/python
import json
import os
import platform
import subprocess
from fabric import Connection
import requests 
from invoke import Exit
import paramiko
import argparse
from config.config import data
import pandas as pd

_PASSWORDS_ = data["PASSWORD"]
_ENDPOINT_ = data["ENDPOINT"]
_ENDPOINT_ALL_CLUSTERS_ = data["ENDPOINT_ALL_CLUSTERS"]
_ENDPOINT_SINGLE_CLUSTER = data["ENDPOINT_SINGLE_CLUSTERS"]  # for this provide cluster id

class Connectivity:
    def __init__(self):
        pass

    def get_xi_data(self):
        """
        function that gets all sites from xi
        :param url: endpoint
        :return: json object containing site details
        """
        response = requests.get(_ENDPOINT_)
        site_data = json.loads(response.content)
        return site_data

    def get_clusters_from_xi(self):
        """Function that gets the clusters from xi"""
        print("getting all clusters")
        response = requests.get(_ENDPOINT_ALL_CLUSTERS_)
        print(response)
        cluster_data = json.loads(response.text)
        return cluster_data

    def get_sites_from_a_cluster(self, cluster_id):
        """This will give you sites primary key under each cluster"""
        response = requests.get(f"{_ENDPOINT_SINGLE_CLUSTER}{cluster_id}")
        single_cluster_data = json.loads(response.text)
        print(single_cluster_data)
        cluster_sites = single_cluster_data[0]["fields"]["site"]
        return cluster_sites

    def check_connectivity_in_all_sites(self):
        print("we are starting")
        _connection_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'cluster-name', 'cluster-pk'])
        _unreachable_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'cluster-name', 'cluster-pk'])

        # first get all clusters from xi
        all_clusters_from_xi = self.get_clusters_from_xi()
        all_sites = self.get_xi_data()

        for cluster in all_clusters_from_xi:
            print("here is the cluster")
            print(cluster)
            pk = cluster["pk"]
            cluster_name = cluster["fields"]["name"]
            
            # get sites from the cluster
            sites_from_the_cluster_pks = self.get_sites_from_a_cluster(pk)

            for each_site_in_cluster_pk in sites_from_the_cluster_pks:
                for site_details_from_xi in all_sites:
                    if site_details_from_xi["pk"] == each_site_in_cluster_pk:
                        site_name = site_details_from_xi["fields"]["name"]
                        site_ip_address = site_details_from_xi["fields"]["ip_address"]
                        site_username = site_details_from_xi["fields"]["username"]
                        # 4. Check if a site is reachable
                        param = '-n' if platform.system().lower() == 'windows' else '-c'

                        if subprocess.call(['ping', param, '1', site_ip_address]) == 0:
                            print("step 1 :  " + site_name + ": is REACHABLE")
                            _connection_report_excel = _connection_report_excel.append({'ip': site_ip_address, 'facility': site_name, 'username': site_username, 'cluster-name': cluster_name, 'cluster-pk': each_site_in_cluster_pk}, ignore_index=True)
                        else:
                            print("*********************************** REACHABLE***********************************")
                            print("step 1 :  " + site_name + ": is NOT REACHABLE")
                            _unreachable_report_excel = _unreachable_report_excel.append({'ip': site_ip_address, 'facility': site_name, 'username': site_username, 'cluster-pk': cluster_name, 'cluster-name': each_site_in_cluster_pk}, ignore_index=True)

        _connection_report_excel.to_excel('Reachable-Report.xlsx', index=False, header=True)
        _unreachable_report_excel.to_excel('unreachable_report_excel.xlsx', index=False, header=True)

        return 1

class SSHKeyPusher:
    def __init__(self, passwords):
        self._PASSWORDS_ = passwords

    def push_ssh_keys(self, cluster_id):
        # Step 1: Get the parameters for sites that are connected
        all_sites = pd.read_excel('./Reachable-Report.xlsx')

        # Step 2: Filter rows based on the provided cluster_id (if cluster_id is not 0)
        if cluster_id != 0:
            reachable_sites = all_sites[all_sites['cluster-pk'] == cluster_id]
        else:
            reachable_sites = all_sites

        # DataFrames to store push results
        _pushed_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'cluster-name', 'cluster-pk'])
        _not_pushed_report_excel = pd.DataFrame(columns=['ip', 'facility', 'username', 'cluster-name', 'cluster-pk'])

        # Step 3: Loop through the connected sites and push ssh keys
        for index, row in reachable_sites.iterrows():
            ip = row['ip']
            facility = row['facility']
            username = row['username']
            cluster_name = row['cluster-name']

            ssh_code_occurrences = []

            for password in self._PASSWORDS_:
                ssh_code = os.system(f"sshpass -p {password} ssh-copy-id -o StrictHostKeyChecking=no {username}@{ip}")
                ssh_code_occurrences.append(ssh_code)

            print(f"All ssh key push test are as follows: {ssh_code_occurrences} and this is for {facility}")
            print("-----DONE-----")

            if 0 in ssh_code_occurrences:
                print(f"********** SUCCESS: Key pushed to {facility} **********")
                _pushed_report_excel = _pushed_report_excel.append({
                    'ip': ip, 'facility': facility, 'username': username, 'cluster-name': cluster_name, 'cluster-pk': cluster_id}, ignore_index=True)
            else:
                print(f"********** FAILURE: Key NOT pushed to {facility} **********")
                _not_pushed_report_excel = _not_pushed_report_excel.append({
                    'ip': ip, 'facility': facility, 'username': username, 'cluster-name': cluster_name, 'cluster-pk': cluster_id
                }, ignore_index=True)

        # Save the results to Excel files
        _not_pushed_report_excel.to_excel('not_pushed_report_excel.xlsx', index=False, header=True)
        _pushed_report_excel.to_excel('pushed_report_excel.xlsx', index=False, header=True)

        return 1

def main():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Add the -h and -l flags
    parser.add_argument("-connect", "--connectivity", action="store_true", help="Simply checks connectivity from XI server")
    parser.add_argument("-ssh", "--sshKeys", action="store_true", help="Pushes ssh keys to sites and check if the server can auto ssh into the sites")

    parser.add_argument("-c", "--cluster_id", type=int, required=True, help="Cluster ID to filter the sites")
    parser.add_argument("-p", "--passwords", type=str, required=True, help="List of passwords to try for SSH")

    args = parser.parse_args()
    
    if args.cluster_id is None:
        raise ValueError("Cluster ID cannot be None. Please provide a valid cluster ID.")

    # Split the passwords into a list
    passwords_list = args.passwords.split(',')

    # Check if passwords have been provided
    if not passwords_list:
        raise ValueError("No passwords provided. Please provide at least one password.")

    if args.connectivity:
        check_connectivity = Connectivity()
        check_connectivity.check_connectivity_in_all_sites()
        print("Checking connectivity")

    if args.sshKeys:
        ssh_pusher = SSHKeyPusher(passwords_list)
        ssh_pusher.push_ssh_keys(cluster_id=args.cluster_id)

if __name__ == "__main__":
    main()
