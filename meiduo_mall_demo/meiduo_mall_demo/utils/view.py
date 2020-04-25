from django import http


# 创建装饰器
def decorater(view):
    def inner(request, *args, **kwargs):
        if request.user.is_authenticated:
            # 用户登录了，执行
            return view(request, *args, **kwargs)
        else:
            # 用户没登录，返回提醒
            return http.JsonResponse({'code': 400, 'errmsg': '请登录后重试'})

    return inner


class LoginRequird(object):
    '''自定义mixin扩展类'''

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        # 调用装饰器过滤状态
        return decorater(view)
