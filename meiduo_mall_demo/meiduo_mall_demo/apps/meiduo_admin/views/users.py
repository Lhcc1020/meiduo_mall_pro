"""
用户查询
    分页
    搜索（过滤）
用户新增

从某一个单一的功能入手。例如 查询用户
- Step 1: 查询所有用户。分析需求，选择视图
- Step 2: 实现分页功能
- Step 3: 实现简单搜索查询

"""
from rest_framework.generics import ListAPIView
from users.models import User
from meiduo_admin.serializers.users import UserModelSerializer

from rest_framework.response import Response
from collections import OrderedDict
from rest_framework.pagination import PageNumberPagination
#  PageNumberPagination 的属性 例如 page_size
#  不能满足我们的需求  pagesize
# 当系统的属性、方法 不能满足我们需求的时候，我们要重写
class PageNum(PageNumberPagination):
    # 默认不传 会返回5条记录。
    # 如果用户传递了 page_size_query_param 对应的数据，就使用用户的
    # 就不用 默认的5条
    page_size = 1

    #https://tieba.baidu.com/p/6699085768?pn=2
    #  page_size_query_param = ‘pn'
    # 前端已经写死了。我们就需要该它  每一页多少条数据的 key
    # pagesize=10
    page_size_query_param = 'pagesize'

    # 最多不超过多少条
    #单页返回的记录条数，最大不超过20，默认为5。
    max_page_size = 2

    def get_paginated_response(self, data):
        return Response({
            'count':self.page.paginator.count,  #用户总量
            'lists':data,     # 分页的结果
            "page": self.page.number,   # 第几页
            "pages": self.page.paginator.num_pages,     # 总页数
            "pagesize": self.page_size   #页容量
        })

"""
前端期望的数据
 {
        "count": "用户总量",
        "lists": [
        ],
        "page": "页码",
        "pages": "总页数",
        "pagesize": "页容量"
      }

我们返回的是
 {
    "count": 3,
    "next": "http://127.0.0.1:8000/meiduo_admin/users/?page=2&pagesize=20000",
    "previous": null,
    "results": [
    ]
}
"""
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import CreateModelMixin
class UserListAPIView(CreateModelMixin,ListAPIView):

    # 根据用户的不同操作，返回不同的查询结果集

    # queryset = User.objects.filter(username__contains='itcast')
    # queryset = User.objects.all()
    # 重写方法
    def get_queryset(self):
        #/meiduo_admin/users/?keyword=<搜索内容>&page=<页码>&pagesize=<页容量>
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return User.objects.filter(username__contains=keyword)
        else:
            return User.objects.all()

    serializer_class = UserModelSerializer

    # 如果在setting中设置了分页类
    # 所有的 二级视图都会添加分页
    # pagination_class
    # 并不是所有的视图都需要添加分页类

    # 哪个视图需要，单独给哪一个视图添加
    # 单独视图添加 分页
    pagination_class = PageNum


    def post(self,request):

        return self.create(request)

from rest_framework.generics import ListCreateAPIView