from django.http import JsonResponse
from django.shortcuts import render
from django import http
from django.views import View
from django_redis import get_redis_connection
import json
from users.models import User
import re
from django.contrib.auth import login, authenticate


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

    def get(self, request, mobile):
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


class Regeist(View):
    '''用户注册，保存信息'''

    def post(self, request):
        '''接收用户信息参数'''
        dic = json.loads(request.body.decode())
        username = dic.get('username')
        password = dic.get('password')
        password2 = dic.get('password2')
        mobile = dic.get('mobile')
        sms_code = dic.get('sms_code')
        allow = dic.get('allow')

        # 检查整体数据是否完整
        if not all([username, password, password2, mobile, sms_code, allow]):
            return http.JsonResponse({'code': 400, 'errmsg': '参数错误，缺少必要参数'})

        # 分步校验
        # 校验用户名
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.JsonResponse({'code': 400, 'errmsg': '用户名格式错误'})
        # 密码格式校验
        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return http.JsonResponse({'code': 400, 'errmsg': '密码格式错误'})

        # 比对密码
        if password2 != password:
            return http.JsonResponse({'code': 400, 'errmsg': '两次输入不相同'})

        # 电话校验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'cede': 400, 'errmsg': '电话号码输入有误'})

        # 协议确认
        if allow != True:
            return http.JsonResponse({'code': 400, 'errmsg': '协议未勾选'})

        # 验证码校验
        # 链接redis
        redis_conn = get_redis_connection('verify_code')

        # 取出需要比对的值
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 判断该值是否存在
        if not sms_code_server:
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码过期'})

        # 校验验证码
        if sms_code_server.decode() != sms_code:
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码有误'})

        # 保存用户信息到数据库
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': '存入数据库出错'})

        # 状态保持
        login(request, user)
        # 返回Json
        return http.JsonResponse({'code': 0, 'errmsg': 'ok'})


class Login(View):
    """登录函数"""

    def post(self, request):
        '''实现用户名登录'''

        # 接受参数
        dir = json.loads(request.body.decode())
        username = dir.get('username')
        password = dir.get('password')
        remembered = dir.get('remembered')

        # 总体检验
        if not all([username, password]):
            return http.JsonResponse({'code': 400, 'errmsg': '关键参数错误'})

        # 校验用户名和密码
        user = authenticate(username=username, password=password)

        # 判断检验结果
        if user is None:
            return http.JsonResponse({'code': 400, 'errmsg': '用户名或者密码错误'})

        # 状态保持
        login(request, user)

        # 判断是否记住状态
        if remembered != True:
            # 浏览器关闭退出登录
            request.session.set_expiry(0)
        else:
            # 保持登录，默认记录两周
            request.session.set_expiry(None)

        # 返回Json
        return http.JsonResponse({'code': 0, 'errmsg': 'ok'})
