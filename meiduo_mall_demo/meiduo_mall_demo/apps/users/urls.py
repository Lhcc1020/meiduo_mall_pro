from django.urls import re_path
from . import views

urlpatterns = [
    # 判断用户名是否重复
    re_path('^usernames/(?P<username>\w{5,20})/count/$',views.UsernameCountView.as_view()),
    re_path('^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.UsermobilPhone.as_view()),
    re_path('^register/$',views.Regeist.as_view()),
    re_path('^login/$',views.Login.as_view()),
    re_path(r'^logout/$', views.LogOut.as_view()),
    re_path(r'^info/$', views.UserInfo.as_view()),
    re_path(r'^emails/$', views.AddEmail.as_view()),
    re_path(r'^emails/verification/$', views.UserEmailActive.as_view()),
    re_path(r'^addresses/create/$', views.Adderss_Add.as_view()),
    re_path(r'^addresses/$', views.Address_View.as_view()),
    re_path(r'^addresses/(?P<address_id>\d+)/$', views.ChangeAddress.as_view()),
    re_path(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddress.as_view()),
    re_path(r'^addresses/(?P<address_id>\d+)/title/$', views.SetAddressTitle.as_view()),
    re_path(r'^password/$', views.ChangePassword.as_view()),
    re_path(r'^browse_histories/$', views.UserBrowseHistory.as_view()),

]
