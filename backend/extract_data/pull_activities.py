#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 18:13:20 2024

@author: emilyfetzner
"""
import pandas as pd
import requests
import urllib3



urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_access_token(client_id, client_secret, refresh_token):
    """
    Request access token from Strava API.

    Args:
        client_id (str): Strava API client ID.
        client_secret (str): Strava API client secret.
        refresh_token (str): Strava API refresh token.

    Returns:
        str: Access token.
    """
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': "refresh_token",
        'f': 'json'
    }
    res = requests.post(auth_url, data=payload, verify=False)
    return res.json()['access_token']

def get_activities(access_token):
    """
    Get activities from Strava API.

    Args:
        access_token (str): Access token.

    Returns:
        list: List of activities.
    """
    activites_url = "https://www.strava.com/api/v3/athlete/activities"
    header = {'Authorization': 'Bearer ' + access_token}
    request_page_num = 1
    all_activities = []

    while True:
        param = {'per_page': 200, 'page': request_page_num}
        my_dataset = requests.get(activites_url, headers=header, params=param).json()

        if len(my_dataset) == 0:
            break

        if all_activities:
            all_activities.extend(my_dataset)
        else:
            all_activities = my_dataset

        request_page_num += 1

    return all_activities

def main():
    CLIENT_ID = "122548"
    CLIENT_SECRET = '608e9ff24f770f3d8f2c0751d230ca1fad409260'
    REFRESH_TOKEN = '64fe5449452cefdf9af2e9de4a0675ce1d4669a0'

    print("Requesting Token...\n")
    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    print("Access Token = {}\n".format(access_token))

    all_activities = get_activities(access_token)
    return all_activities

if __name__ == "__main__":
    main()
