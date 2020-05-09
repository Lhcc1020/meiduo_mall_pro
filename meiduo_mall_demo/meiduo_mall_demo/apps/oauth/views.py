import json
import re

from django.shortcuts import render
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import http
from django.views import View
import logging
from django.contrib.auth import login
from django_redis import get_redis_connection

from carts.utils import merge_cart_cookie_to_redis
from oauth.models import OAuthQQuser
from oauth.utils import generate_access_token, check_access_token
from users.models import User

logger = logging.getLogger('django')

class QQUrl(View):
    '''响应QQ登录页面地址'''

    def get(self, request):
        # next 表示从哪个页面进入到的登录页面
        # 将来登录成功后，就自动回到那个页面
        next = request.GET.get('next')


        # 获取qq登录网址
        # 创建 ouath对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)
        # 通过对象调用方法获取url
        login_url = oauth.get_qq_url()

        # 返回对应地址
        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok',
                                  'login_url': login_url})


class QQUserlogreturn(View):
    '''用户QQ登录回调'''
    def get(self, request):
        '''Oauth2.0验证'''

        # 获取前段传的code
        code = request.GET.get('code')

        if not code:
            return http.JsonResponse({'code': 400, 'errmsg': '缺少code参数'})

        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 使用code向QQ请求access_token
            access_token = oauth.get_access_token(code)

            # 使用access_token请求openid
            openid = oauth.get_open_id(access_token)

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': 'oauth2.0验证失败，QQ信息获取失败'})


        # 根据openid查询用户是否第一次绑定
        try:
            oauth_qq = OAuthQQuser.objects.get(openid=openid)
        except Exception as e:
            access_token = generate_access_token(openid)

            # 把 access_token 返回给前端
            # 注意: 这里一定不能返回 0 的状态码. 否则不能进行绑定页面
            return http.JsonResponse({'code': 300,
                                      'errmsg': 'ok',
                                      'access_token': access_token})

        else:

            # openid 已绑定美多商城用户,根据 user 外键, 获取对应的 QQ 用户(user)
            user = oauth_qq.user

            # 状态保持
            login(request, user)

            # 创建重定向到主页的对象
            response = http.JsonResponse({'code': 0,
                                          'errmsg': 'ok'})

            # 将用户信息写入到 cookie 中，有效期14天
            response.set_cookie('username',
                                user.username,
                                max_age=3600 * 24 * 14)

            response = merge_cart_cookie_to_redis(request, response)
            # 返回响应
            return response


    def post(self, request):
        '''openid绑定用户信息'''

        # 接受参数
        dict = json.loads(request.body.decode())
        mobile = dict.get('mobile')
        password = dict.get('password')
        sms_code_client = dict.get('sms_code')
        access_token = dict.get('access_token')

        # 校验参数
        if not all([mobile, password, sms_code_client, access_token]):
            return http.JsonResponse({'code': 400, 'errmsg': '参数有误'})

        # 手机号校验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400, 'errmsg': '请输入正确手机号-'})

        # 密码校验
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '请按要求正确输入密码'})

        # 短信验证码比对
           # 创建redis对象
        redis_conn = get_redis_connection('verify_code')

        # 从redis获取验证码
        sms_code_sever = redis_conn.get('sms_%s' % mobile)

        # 判断验证码是否失效
        if sms_code_sever == None:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '短信验证码失效'})

        # 判断验证码是否正确
        if sms_code_client != sms_code_client:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '短信验证码错误'})

        # 判断access_token
        # 调用自定义的函数
        openid = check_access_token(access_token)

        if not openid:
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'openid缺失'})

        # 保存用户注册信息
        try:
            # 通过手机号先读取用户信息
            user = User.objects.get(mobile=mobile)

        except Exception as e:
            # 读不到用户，创建新用户保存
            user = User.objects.create_user(username=mobile,
                                            mobile=mobile,
                                            password=password)
        else:
            # 用户存在验证用户密码
            if not user.check_password(password):
                return http.JsonResponse({'code': 400,
                                      'errmsg': '用户密码错误'})

        # 将openid绑定到用户信息
        try:
            OAuthQQuser.objects.create(openid=openid, user=user)

        except Exception as e:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '数据库添加错误'})

        # 登录保持
        login(request, user)

        # 创建响应对象
        response = http.JsonResponse({'code': 0,
                                      'errmsg': 'ok'})

        # 将用户信息写入到 cookie 中，有效期14天
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)

        response = merge_cart_cookie_to_redis(request, response)
        # 返回响应
        return response

