from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^qq/authorization/$', views.QQUrl.as_view()),
    re_path(r'^oauth_callback/$', views.QQUserlogreturn.as_view()),
]
