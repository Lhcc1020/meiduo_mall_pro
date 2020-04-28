from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


# 我们重写用户模型类, 继承自 AbstractUser
class User(AbstractUser):
    """自定义用户模型类"""

    # 额外增加 mobile 字段，使用字符串格式
    mobile = models.CharField(
        # 长度限制11位
        max_length=11,
        # 唯一
        unique=True,
        verbose_name='手机号')

    email_active = models.BooleanField(default=False,
                                       verbose_name='邮箱验证状态')

    # 对当前表进行相关设置:
    class Meta:
        # 设置表名
        db_table = 'tb_users'
        # 表中文名
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    # 在 str 魔法方法中, 返回用户名称
    def __str__(self):
        return self.username


    def make_token_value(self):
        '''生成邮箱验证链接'''
        obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=1800)

        # 将用户名和邮箱加入加密链接中
        dirt = {'user_id': self.id,
                'email': self.email}

        token = obj.dumps(dirt).decode()

        return settings.EMAIL_VERIFY_URL + token

   # 定义静态函数用于验证邮箱激活确认
    @staticmethod
    def check_email(token):
        # 获取token提取user，验证user，确认激活邮箱，修改数据库状态
        obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=1800)
        try:
            # 通过传如的token获取user
            user_data = obj.loads(token)

        except Exception as e:
            # 获取出错，返回空值
            return None

        # 获取到用户数据，提取id，邮箱
        user_id = user_data.get('user_id')
        user_email = user_data.get('email')

        try:
            # 尝试获取数据库中对应用户信息
            user = User.objects.get(id=user_id,email=user_email)

        except Exception as e:
            # 用户信息不存在
            return None

        # user信息存在，返回user
        return user