from rest_framework import serializers
from goods.models import SKUImage

class ImageModelSerializer(serializers.ModelSerializer):

    # 默认是获取外键值
    # 我们最终要获取 管理的模型的字符串的内容
    sku = serializers.StringRelatedField(label='sku管理的模型__str__的内容')

    class Meta:
        model=SKUImage
        fields = ['id','sku','image']

from goods.models import SKU
class SimpleSKUModleSerializer(serializers.ModelSerializer):
    """
    虽然选择的时候是选择的名字
    但是我们保存数据的时候 肯定是保存的sku的id
    'id','name'
    """
    class Meta:
        model = SKU
        fields = ['id','name']