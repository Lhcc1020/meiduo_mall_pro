from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django import http
from django.views import View
from django_redis import get_redis_connection
import json
from celery_tasks.email.tasks import send_verify_email
from meiduo_mall_demo.utils.view import LoginRequird
from users.models import User
import re
from django.contrib.auth import login, authenticate, logout
import logging

logger = logging.getLogger('django')


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

        # 定义相应对象
        response = http.JsonResponse({'code': 0, 'errmsg': 'ok'})

        # 设置cookie ，时限14天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

        # 返回Json
        return response


class LogOut(View):
    '''创建一个登出接口'''
    def delete(self, request):

        # 使用logout登出
        logout(request)

        # 创建返回对象
        response = http.JsonResponse({'code': 0, 'errmsg': 'ok'})

        # 清除cookie
        response.delete_cookie('username')

        # 返回响应
        return response


class UserInfo(LoginRequird, View):
    # 用户中心
    def get(self, request):
        '''只有登录用户才能进入该类视图'''

        info_data = {
            'username': request.user.username,
            "mobile": request.user.mobile,
            "email": request.user.email,
            "email_active": request.user.email_active
        }

        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok',
                                  'info_data': info_data})


class AddEmail(View):
    '''添加邮箱信息'''

    def put(self, request):
        # 接受参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return http.JsonResponse({'code': 400, 'errmsg': '缺少邮箱参数'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '邮箱参数有误'})
        # 添加邮箱信息到数据库
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                      'errmsg': '保存邮箱到数据库出错'})

        # 发送验证邮件到当前用户邮箱
        # 将验证链接生成
        verify_url = request.user.make_token_value()
        # 发送验证邮件
        send_verify_email.delay(email, verify_url)

        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok'})

class UserEmailActive(View):
    '''邮箱激活验证'''
    def put(self, request):

        # 接受参数
        token = request.GET.get('token')

        # 检验参数
        if not token:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少token'})

        # token存在
        # 调用函数，提取user信息
        user = User.check_email(token)
        if not user:
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'token无效'})

        try:
            # user获取正常，修改email_active,保存
            user.email_active = True
            user.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                      'errmsg': '邮箱激活失败'})

            # 返回邮箱验证结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok'})
