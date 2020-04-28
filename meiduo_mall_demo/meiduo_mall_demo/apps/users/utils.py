from django.contrib.auth.backends import ModelBackend
import re
from .models import User


def checkusername(account):
    '''判断accout是手机号还是用户名'''
    # 操作数据库放在try中
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile = account)
        else:
            user = User.objects.get(username=account)
    except Exception as e:
        return None

    else:
        return user


class UsernameCheck(ModelBackend):
    """自定义用户认证后端,继承ModelBackend"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 重写继承的认证方法
        user = checkusername(username)

        # 确认判断结果,并校验密码
        if user and user.check_password(password):
            return user


