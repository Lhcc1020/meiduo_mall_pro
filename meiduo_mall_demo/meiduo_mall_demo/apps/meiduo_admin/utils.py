def jwt_response_payload_handler(token, user=None, request=None):
    #token, user=None, request=None
    #token,             已经认证成功之后，生成的token
    # user=None,        已经认证成功之后，用户实例对象
    # request=None      登录的请求实例
    print('aaa')
    return {
        'token': token,
        'user_id':user.id,
        'username':user.username
    }


from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
#  PageNumberPagination 的属性 例如 page_size
#  不能满足我们的需求  pagesize
# 当系统的属性、方法 不能满足我们需求的时候，我们要重写
class PageNum(PageNumberPagination):
    # 默认不传 会返回5条记录。
    # 如果用户传递了 page_size_query_param 对应的数据，就使用用户的
    # 就不用 默认的5条
    page_size = 10

    #https://tieba.baidu.com/p/6699085768?pn=2
    #  page_size_query_param = ‘pn'
    # 前端已经写死了。我们就需要该它  每一页多少条数据的 key
    # pagesize=10
    page_size_query_param = 'pagesize'

    # 最多不超过多少条
    #单页返回的记录条数，最大不超过20，默认为5。
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response({
            'count':self.page.paginator.count,  #用户总量
            'lists':data,     # 分页的结果
            "page": self.page.number,   # 第几页
            "pages": self.page.paginator.num_pages,     # 总页数
            "pagesize": self.page_size   #页容量
        })