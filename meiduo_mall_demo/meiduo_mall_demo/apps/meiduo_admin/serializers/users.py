from rest_framework import serializers
from users.models import User

"""
serializers.Serializer
serializers.ModelSerializer
    ModelSerializer与常规的Serializer相同，但提供了：

    基于模型类自动生成一系列字段

    包含默认的create()和update()的实现
"""
class UserModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        # fields = '__all__'        # 最简单 最偷懒的方法
        fields = ['id','username','mobile','email','password']

        # password 应该只在 反序列化的时候使用
        extra_kwargs = {
            'password': {
                'write_only':True,
                'min_length':8,
                'max_length':20
            }
        }

    def create(self, validated_data):

        return User.objects.create_user(**validated_data)