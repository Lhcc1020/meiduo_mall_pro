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
        obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=1800)

        dirt = {'user': self.id,
                'email': self.email}

        token = obj.dumps(dirt).decode()

        return settings.EMAIL_VERIFY_URL + token
