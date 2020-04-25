from django.db import models

# 定义模型类
class BaseModel(models.Model):

    # 添加创建时间
    create_time = models.DateTimeField(auto_now_add=True,
                                       verbose_name='创建时间')
    # 添加更新时间
    update_time = models.DateTimeField(auto_now=True,
                                       verbose_name='更新时间')

    class Meta:
        # 表名抽象类，迁移时不生成表格
        abstract = True