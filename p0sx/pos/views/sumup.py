from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction as django_transaction, IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from urllib.parse import urlencode

from django_q.tasks import async_task

from ..models.stock import Order, PaymentState, OrderState
from ..models.sumup_cloud import SumupTransaction, SumupAuthorization
from ..service.sumup import get_sumup_transaction

import json
import logging

logger = logging.getLogger(__name__)


SUMUP_SCOPES = []
SUMUP_AUTHZ_URL = "https://api.sumup.com/authorize"


@csrf_exempt
def sumup_ordercallback(request, order_id):
    callback = json.loads(request.body)
    transaction_id = callback['payload']['client_transaction_id']
    logger.debug(callback)

    try:
        order = Order.objects.get(pk=order_id, payment_reference=transaction_id)
        transaction = get_sumup_transaction(transaction_id)
        logger.debug(transaction)
        transaction_status = None if transaction is None else transaction['status']
        if transaction_status == 'SUCCESSFUL':
            order.payment_state = PaymentState.Paid
            if order.state == OrderState.Open:
                async_task("pos.services.print_pickup_receipts", order.id,
                           task_name='Pickup receipts for order {id}'.format(id=order.id))
            order.save()
        elif transaction_status == 'FAILED':
            order.payment_state = PaymentState.Failed
            order.save()
        elif transaction_status == 'CANCELLED':
            order.payment_state = PaymentState.Cancelled
            order.save()
        elif transaction_status == 'PENDING':
            logger.info(f"Payment for order {order_id} is still pending...")

        return HttpResponse('OK')
    except:
        logger.error(f"pk: {order_id} client_transaction_id: '{transaction_id}' failed to get order")
        return HttpResponse(status=500)

@csrf_exempt
def sumup_creditcallback(request, transaction_id):
    callback = json.loads(request.body)
    client_transaction_id = callback['payload']['client_transaction_id']
    logger.debug(callback)

    try:
        transaction = SumupTransaction.objects.get(pk=transaction_id, payment_reference=client_transaction_id)
        sumup_transaction = get_sumup_transaction(client_transaction_id)
        logger.debug(sumup_transaction)
        transaction_status = None if sumup_transaction is None else sumup_transaction['status']
        if transaction_status == 'SUCCESSFUL':
            try:
                with django_transaction.atomic():
                    transaction.payment_state = PaymentState.Paid
                    if not transaction.used:
                        transaction.used = True
                        transaction.user.credit += transaction.amount
                        transaction.user.save()
                    transaction.save()
            except IntegrityError:
                return HttpResponse(status=500)
        elif transaction_status == 'FAILED':
            transaction.payment_state = PaymentState.Failed
            transaction.save()
        elif transaction_status == 'CANCELLED':
            transaction.payment_state = PaymentState.Cancelled
            transaction.save()
        elif transaction_status == 'PENDING':
            logger.info(f"Payment for transaction {transaction_id} is still pending...")

        return HttpResponse('OK')
    except:
        logger.error(f"pk: {transaction_id} client_transaction_id: '{client_transaction_id}' failed to get transaction")
        return HttpResponse(status=500)


def _get_redirect_url(request):
    # TODO: Base this on url path name instead
    return request.build_absolute_uri("/littleadmin/sumup-return/")


def _get_authz_url(request, nonce):
    params = {
        "response_type": "code",
        "client_id": settings.SUMUP_CLIENT_ID,
        "redirect": _get_redirect_url(request),
        "scopes": " ".join(SUMUP_SCOPES),
        "state": nonce
    }
    return f"{SUMUP_AUTHZ_URL}?{urlencode(params)}"


@login_required
def sumup_oauth_init(request):
    auth_obj = SumupAuthorization()
    sumup_authz_url = _get_authz_url(request, auth_obj.nonce)
    return redirect(sumup_authz_url)


@csrf_exempt
def sumup_oauth_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")
    auth_obj = get_object_or_404(SumupAuthorization, refresh_token=None, nonce=state)
    refresh_token, expiry = get_sumup_refresh_token(code, request.build_full_uri())
    auth_obj.refresh_token = refresh_token
    auth_obj.expiry = expiry
    auth_obj.save()
    return HttpResponse("ok")
