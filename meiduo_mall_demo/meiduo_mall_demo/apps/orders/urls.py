from django.urls import re_path
from . import views

urlpatterns = [
    # 订单提交
    re_path(r'^orders/commit/$', views.OrderCommitView.as_view()),
    # 订单确认
    re_path(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
]
