import requests
from datetime import datetime, timedelta
from typing import Optional
from django.core.exceptions import ValidationError
from django.conf import settings

from urllib.parse import urljoin


API_URL = 'https://api.sumup.com/'
_TOKEN_URL = urljoin(API_URL, "/token")

def get_sumup_client_token():
    data = {"grant_type": "client_credentials"}
    auth = (settings.SUMUP_CLIENT_ID, settings.SUMUP_CLIENT_SECRET)

    response = requests.post(_TOKEN_URL, data=data, auth=auth)
    response.raise_for_status()

    ret = response.json()
    access_token = ret["access_token"]
    return access_token


def get_sumup_refresh_token(authz_code, redirect_uri):
    data = {
        "grant_type": "authorization_code",
        "code": authz_code,
        "redirect_uri": redirect_uri,
        "client_id": settings.SUMUP_CLIENT_ID,
        "client_secret": settings.SUMUP_CLIENT_SECRET
    }
    response = requests.post(_TOKEN_URL, data=data)
    response.raise_for_status()

    ret = response.json()
    refresh_token = ret["refresh_token"]
    # TODO: Extract refresh token validity
    expires = datetime.now() + timedelta(days=7)
    return refresh_token, expires


def get_access_token():
    from ..models.sumup_cloud import SumupAuthorization
    authz = SumupAuthorization.objects.filter(refresh_token__isnull=False, expiry__gt=datetime.now()).first()
    if not authz:
        raise Exception("No authorization found, go to /littleadmin/sumup/oauth/init/ to fix")

    data = {
        "grant_type": "refresh_token",
        "refresh_token": authz.refresh_token,
        "client_id": settings.SUMUP_CLIENT_ID,
        "client_secret": settings.SUMUP_CLIENT_SECRET
    }
    response = requests.post(_TOKEN_URL, data=data)
    response.raise_for_status()

    ret = response.json()
    refresh_token = ret["refresh_token"]
    expires = datetime.now() + timedelta(seconds=ret["expires_in"])
    return refresh_token, expires


class SumupClient:
    i_access_token: str
    merchant_code: str

    def __init__(self):
        self._client_access_token = get_access_token()
        self.merchant_code = settings.SUMUP_MERCHANT_CODE

    @staticmethod
    def _get_url(path):
        base_url =  urljoin(API_URL, "/v0.1/")
        return urljoin(base_url, path)

    def _get_merchant_url(self, path):
        merchant_base = self._get_url(f"merchants/{settings.SUMUP_MERCHANT_CODE}/")
        return urljoin(merchant_base, path)

    def request(self, url: str, method: str = "GET", data: Optional[dict] = None, params: Optional[dict] = None):
        data = data or {}
        params = params or {}
        headers = {
            "Authorization": f"Bearer {self._access_token}",
        }
        return requests.request(method, url, json=data, params=params)

    def pair_sumup_reader(self, name, pairing_code):
        data = {
            "name": name,
            "pairing_code": pairing_code,
        }
        url = self._get_merchant_url("readers")
        return self.request(url, method="POST", data=data)

    def delete_reader(self, reader_id):
        url = self._get_merchant_url(f"readers/{reader_id}")
        return self.request(url, method="DELETE")


def init_order_card_payment(order, reader_id):
    """
    Initializes payment with a SumUp terminal
    """
    payload = {
        "total_amount": {"value": int(order.sum * 100), "currency": "NOK", "minor_unit": 2},
        "description": f"{settings.EVENT_NAME} p0sX ordre {order.pk}",
        "return_url":  settings.SUMUP_CALLBACK_HOSTNAME + '/order-callback/' + str(order.pk),
    }
    url = f"https://api.sumup.com/v0.1/merchants/{settings.SUMUP_MERCHANT_CODE}/readers/{reader_id}/checkout"
    headers = {"Authorization": f"Bearer {settings.SUMUP_BEARER_TOKEN}"}
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 201:
        raise ValidationError(f"Unexpected status code from SumUp {response.status_code}")
    order.payment_reference = response.json()["data"]["client_transaction_id"]
    order.save()


def init_credit_fill_payment(transaction, reader_id):
    """
    Initializes payment with a SumUp terminal
    """
    payload = {
        "total_amount": {"value": int(transaction.amount * 100), "currency": "NOK", "minor_unit": 2},
        "description": f"{settings.EVENT_NAME} P0sX påfyll for {transaction.user.card} - {transaction.pk}",
        "return_url":  settings.SUMUP_CALLBACK_HOSTNAME + '/credit-callback/' + str(transaction.pk),
    }
    url = f"https://api.sumup.com/v0.1/merchants/{settings.SUMUP_MERCHANT_CODE}/readers/{reader_id}/checkout"
    headers = {"Authorization": f"Bearer {settings.SUMUP_BEARER_TOKEN}"}
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 201:
        raise ValidationError(f"Unexpected status code from SumUp {response.status_code}")
    transaction.payment_reference = response.json()["data"]["client_transaction_id"]
    transaction.save()


def get_sumup_transaction(transaction_id):
    headers = {"Authorization": f"Bearer {settings.SUMUP_BEARER_TOKEN}"}
    url = f"https://api.sumup.com/v2.1/merchants/{settings.SUMUP_MERCHANT_CODE}/transactions?client_transaction_id={transaction_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


# def pair_sumup_reader(name, pairing_code):
#     client = SumupClient()
#     response = client.pair_sump_reader(name, pairing_code)
#     if response.status_code == 201:
#         return response.json()["id"]
#     return None
# 
# 
# def delete_sumup_reader(reader_id):
#     client = SumupClient()
#     response = client.delete_sumup_reader(reader_id)
#     return response.status_code
    

def pair_sumup_reader(name, pairing_code):
    payload = {
        "name": name,
        "pairing_code": pairing_code
    }
    url = f"https://api.sumup.com/v0.1/merchants/{settings.SUMUP_MERCHANT_CODE}/readers"
    headers = {"Authorization": f"Bearer {settings.SUMUP_BEARER_TOKEN}"}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        return response.json()["id"]
    return None


def delete_sumup_reader(reader_id):
    url = f"https://api.sumup.com/v0.1/merchants/{settings.SUMUP_MERCHANT_CODE}/readers/{reader_id}"
    headers = {"Authorization": f"Bearer {settings.SUMUP_BEARER_TOKEN}"}
    response = requests.delete(url, headers=headers)
    return response.status_code

