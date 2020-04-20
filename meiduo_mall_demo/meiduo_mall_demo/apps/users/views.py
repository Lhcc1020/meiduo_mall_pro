from django.http import JsonResponse
from django.shortcuts import render
from django import http
# Create your views here.
from django.views import View

from users.models import User


class UsernameCountView(View):
    '''判断用户名是否已经使用'''
    def get(self, request, username):
        '''判断是否重复'''
        try:
            # 判断数据库中用户名个数
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '访问数据库失败'})
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count': count})

class UsermobilPhone(View):
    '''手机号判断'''
    def get(self,request, mobile):
        '''检验手机号是否重复'''
        try:
            # 判断手机号个数
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '数据查询错误'})
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count': count})