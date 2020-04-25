from django.db import models
from meiduo_mall_demo.utils.BaseModel import BaseModel



# 定义QQ登录的模型类
class OAuthQQuser(BaseModel):
    '''用户QQ登录'''
    # user外键，关联用户本地信息
    user = models.ForeignKey('users.User',
                             on_delete=models.CASCADE,
                             verbose_name='用户')

    # QQ给的openid
    openid = models.CharField(max_length=64,
                              verbose_name='openid',
                              db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户信息'
        verbose_name_plural = verbose_name
