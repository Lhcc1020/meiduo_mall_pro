from django.shortcuts import render

import os
from alipay import AliPay
from django.http import JsonResponse
from django.views import View
from orders.models import OrderInfo
from django.conf import settings

class PaymentView(View):
    """订单支付功能"""

    def get(self,request, order_id):
        # 查询要支付的订单
        user = request.user

        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                         status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':'order_id有误'})

        # 创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG
        )

        # 生成登录支付宝连接
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        # 响应登录支付宝连接
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + "?" + order_string
        return JsonResponse({'code': 0,
                             'errmsg': 'OK',
                             'alipay_url': alipay_url})