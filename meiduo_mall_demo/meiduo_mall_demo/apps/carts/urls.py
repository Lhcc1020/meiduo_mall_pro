from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^carts/$', views.CartsView.as_view()),
    re_path(r'^carts/selection/$', views.CartSelectAllView.as_view()),
    # 提供商品页面右上角购物车数据
    re_path(r'^carts/simple/$', views.CartsSimpleView.as_view()),

]
