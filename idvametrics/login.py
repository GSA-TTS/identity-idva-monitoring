"""
Provides functions for logging into a Ping environment.
"""

import sys
import requests
import pyotp


def get_login(email: str, password: str, base_url: str, totp: str):
    """
    Returns the auth header, which contains an access token, of an SFA login attempt. If
    MFA is required, returns the auth head of an MFA login attempt.
    """
    login_path = "/v1/customers/login"
    login_data = {"email": email, "password": password}

    login_response = requests.post(base_url + login_path, json=login_data)
    if login_response.status_code != 200:
        print(login_response.json())
        sys.exit(login_response.status_code)

    login_response = login_response.json()
    access_token = login_response["access_token"]
    callback_header = {"Authorization": f"Bearer {access_token}"}

    if not "mfaRequired" in login_response.keys() or not login_response["mfaRequired"]:
        return callback_header

    otp = pyotp.TOTP(totp).now()
    mfa_login_response = mfa_flow(base_url, login_response, otp)
    skcallback_data = mfa_login_response

    callback_path = "/v1/customers/skcallback"

    callback_response = requests.post(
        base_url + callback_path, json=skcallback_data, headers=callback_header
    )

    if callback_response.status_code != 200:
        print(callback_response.json())
        sys.exit(callback_response.status_code)

    return {"Authorization": f"Bearer {callback_response.json()['access_token']}"}


def mfa_flow(base_url, login_response, otp):
    """
    Runs the Ping MFA flow to obtain an MFA response which contains an access token.
    """
    company_id = login_response["companyId"]
    mfa_access_token = login_response["skSdkToken"]["access_token"]

    mfa_policy_path = (
        f"/v1/auth/{company_id}/policy/{login_response['flowPolicyId']}/start"
    )

    # obtaining json definition of the mfa flow
    policy_response = requests.post(
        base_url + mfa_policy_path,
        headers={"Authorization": f"Bearer {mfa_access_token}"},
    ).json()

    capability_name = policy_response["screen"]["properties"]["mfaList"]["value"][0][
        "capabilityName"
    ]
    connection_id = policy_response["screen"]["properties"]["mfaList"]["value"][0][
        "connectionId"
    ]

    mfa_init_data = {
        "parameters": {},
        "onLoadEvent": {
            "params": ["phoneNumber"],
            "eventName": "authInitiate",
            "eventType": "post",
            "constructType": "skEvent",
        },
        "eventName": "authInitiate",
        "connectionId": connection_id,
        "capabilityName": capability_name,
        "userViewIndex": 0,
        "id": policy_response["id"],
    }

    mfa_login_path = (
        f"/v1/auth/{company_id}"
        f"/connections/{connection_id}/capabilities/{capability_name}"
    )

    mfa_login_headers = {
        "interactionId": policy_response["interactionId"],
        "interactionToken": policy_response["interactionToken"],
    }

    # First step in the mfa flow, obtaining one in a list of MFA providers
    mfa_init_response = requests.post(
        base_url + mfa_login_path, json=mfa_init_data, headers=mfa_login_headers
    ).json()

    mfa_login_data = {
        "parameters": {
            "otp": otp,
            "challenge": mfa_init_response["challenge"],
        },
        "nextEvent": {
            "eventName": "authComplete",
            "eventType": "post",
            "constructType": "skEvent",
        },
        "eventName": "authComplete",
        "connectionId": connection_id,
        "capabilityName": capability_name,
        "userViewIndex": 0,
        "id": policy_response["id"],
    }

    # submits the OTP
    mfa_login_response = requests.post(
        base_url + mfa_login_path, json=mfa_login_data, headers=mfa_login_headers
    )

    if mfa_login_response.status_code != 200:
        print(mfa_login_response.json())
        sys.exit(mfa_login_response.status_code)

    return mfa_login_response.json()
