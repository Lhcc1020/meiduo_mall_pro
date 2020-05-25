from rest_framework_jwt.views import obtain_jwt_token
from django.conf.urls import re_path
#obtain_jwt_token 就是　验证用户名和密码，没有问题，会返回Ｔｏｋｅｎ
# 就是后台登录接口
from .views import home,users,image
from rest_framework.routers import DefaultRouter

# meiduo_admin/authorizations/
# Vue 已经把 JS写死了 路由只能按照笔记中
urlpatterns = [
    # 先复制过来，看看能不能实现
    # obtain_jwt_token APIView
    # ObtainJSONWebToken.as_view()
    re_path(r'^authorizations/$',obtain_jwt_token),

    re_path(r'^statistical/total_count/$',home.TotalCountView.as_view()),
    re_path(r'^statistical/day_active/$',home.UserDayActiveAPIView.as_view()),
    re_path(r'^statistical/day_orders/$',home.UserOrderInfoCountAPIView.as_view()),
    re_path(r'^statistical/month_increment/$',home.MonthUserView.as_view()),

    # 用户管理
    re_path(r'^users/$',users.UserListAPIView.as_view()),
    # 图片管理
    re_path(r'^skus/simple/$',image.SimpleSKUListAPIView.as_view()),

]
"""
默认是返回token
需求是： 不仅要返回token，还需要 user_id username

根据文档： 自定义一个方法，然后通过配置信息来加载我们的自定义方法
"""
# 1.创建router实例
router = DefaultRouter()
# 2.注册路由
router.register('skus/images',image.ImageModelViewSet,basename='images')
#3.将router生成的路由 追加到 urlpatterns中
urlpatterns += router.urls
