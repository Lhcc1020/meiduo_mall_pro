import base64
import json
import pickle

from django.http import JsonResponse
from django.views import View
from django_redis import get_redis_connection


from goods.models import SKU


class CartsView(View):
    """购物车管理"""

    def post(self, request):
        '''接收购物车参数,保存'''

        # 1.接收json参数
        dict = json.loads(request.body.decode())
        sku_id = dict.get('sku_id')
        count = dict.get('count')
        selected = dict.get('selected', True)

        # 2.总体检验是否为空
        if not all([sku_id, count]):
            return JsonResponse({'code': 400,
                                 'errmsg': '必传参数为空'})

        # 3.单个检验sku_id是否存在
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': 'sku_id参数有误'})

        # 4.count是否是个数字
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': 'count参数有误'})

        # 5.判断selected是否存在,如果存在,是不是bool值
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400,
                                     'errmsg': 'selected参数有误'})

        # 6.判断用户是否登录,
        if request.user.is_authenticated:
            # 8.如果用户登录, 进入这里
            # 9.链接redis, 获取链接对象
            redis_conn = get_redis_connection('carts')

            # 10.往redis的hash中增加数据: carts_user_id : {sku_id : count}
            redis_conn.hincrby('carts_%s' % request.user.id,
                               sku_id,
                               count)

            # 11.往redis的set中增加数据: selected_user_id:{sku_id1, sku_id2, ...}
            redis_conn.sadd('selected_%s' % request.user.id,
                            sku_id)

            # 12.返回json结果
            return JsonResponse({'code': 0,
                                 'errmsg': 'ok'})

        else:
            # 7.如果没有登录, 进入这里
            # 13.从cookie中获取对应的数据
            cart_cookie = request.COOKIES.get('carts')

            # 14.判断该数据是否存在, 如果存在, 解密 ===> dict
            if cart_cookie:
                cart_dict = pickle.loads(base64.b64decode(cart_cookie))
            else:
                # 15.如果不存在, 创建一个新的dict
                cart_dict = {}

            # 16.判断sku_id是否存在于dict中
            if sku_id in cart_dict:
                # 17.如果在, count要进行累加
                count += cart_dict[sku_id]['count']

            # 18.更新字典
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 19.把dict加密, 得到加密的结果
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response = JsonResponse({'code': 0,
                                     'errmsg': 'Ok'})

            # 20.把加密的结果, 写入到cookie
            response.set_cookie('carts', cart_data, max_age=3600 * 24 * 14)

            # 21.返回响应(cookie)
            return response

    def get(self, request):
        """展示购物车"""
        user = request.user
        if user.is_authenticated:
            # 用户已登录，查询 redis 购物车
            redis_conn = get_redis_connection('carts')
            # 获取 redis 中的购物车数据
            item_dict = redis_conn.hgetall('carts_%s' % user.id)
            # 获取 redis 中的选中状态
            cart_selected = redis_conn.smembers('selected_%s' % user.id)

            # 将 redis 中的数据构造成跟 cookie 中的格式一致
            # 方便统一查询
            cart_dict = {}
            for sku_id, count in item_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in cart_selected
                }
        else:
            # 用户未登录，查询cookies购物车
            # 用户未登录，查询cookies购物车
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                # 将cart_str转成bytes,再将bytes转成base64的bytes,
                # 最后将bytes转字典
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        cart_skus = []
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'selected': cart_dict.get(sku.id).get('selected'),
                'default_image_url': sku.default_image_url,
                'price': sku.price,
                'amount': sku.price * cart_dict.get(sku.id).get('count'),
            })

            # 渲染购物车页面
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'cart_skus': cart_skus})

    def put(self, request):
        """修改购物车"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 判断参数是否齐全
        if not all([sku_id, count]):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数有误'})
        # 判断sku_id是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': 'sku_id参数有误'})
        # 判断count是否为数字
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'code': 400,
                                 'errmsg': 'count参数有误'})
        # 判断selected是否为bool值
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code': 400,
                                     'errmsg': 'selected参数有误'})

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，修改redis购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 因为接口设计为幂等的，直接覆盖
            pl.hset('carts_%s' % user.id, sku_id, count)
            # 是否选中
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

            # 创建响应对象
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected,
                'name': sku.name,
                'default_image_url': sku.default_image_url,
                'price': sku.price,
                'amount': sku.price * count,
            }
            return JsonResponse({'code': 0,
                                 'errmsg': '修改购物车成功',
                                 'cart_sku': cart_sku})
        else:
            # 用户未登录，修改cookie购物车
            # 用户未登录，修改cookie购物车
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                # 将cookie_cart转成bytes,再将bytes转成base64的bytes,最后将bytes转字典
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}
            # 因为接口设计为幂等的，直接覆盖
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将字典转成bytes,再将bytes转成base64的bytes,最后将bytes转字符串
            cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

            # 创建响应对象
            cart_sku = {
                'id': sku_id,
                'count': count,
                'selected': selected
            }
            response = JsonResponse({'code': 0,
                                     'errmsg': '修改购物车成功',
                                     'cart_sku': cart_sku})
            # 响应结果并将购物车数据写入到cookie
            response.set_cookie('carts', cart_data)

            return response

    def delete(self, request):
        """删除购物车"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 判断sku_id是否存在
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': 'Sku_id错误'})

        # 判断用户是否登录
        user = request.user
        if user is not None and user.is_authenticated:
            # 用户未登录，删除redis购物车
            # 用户未登录，删除redis购物车
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 删除键，就等价于删除了整条记录
            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()

            # 删除结束后，没有响应的数据，只需要响应状态码即可
            return JsonResponse({'code': 0,
                                 'errmsg': '删除购物车成功'})
        else:
            # 用户未登录，删除cookie购物车
            # 用户未登录，删除cookie购物车
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                # 将cookie_cart转成bytes,再将bytes转成base64的bytes,最后将bytes转字典
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
            else:
                cart_dict = {}

            # 创建响应对象
            response = JsonResponse({'code': 0,
                                     'errmsg': '删除购物车成功'})
            if sku_id in cart_dict:
                del cart_dict[sku_id]
                # 将字典转成bytes,再将bytes转成base64的bytes,最后将bytes转字符串
                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()
                # 响应结果并将购物车数据写入到cookie
                response.set_cookie('carts', cart_data)

            return response

class CartSelectAllView(View):
    """全选购物车"""

    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected', True)

        # 校验参数
        if selected:
            if not isinstance(selected, bool):
                return JsonResponse({'code':'400',
                                     'errmsg': 'selected参数错误'})

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录，操作redis购物车
            # 用户已登录，操作 redis 购物车
            redis_conn = get_redis_connection('carts')
            item_dict = redis_conn.hgetall('carts_%s' % user.id)
            sku_ids = item_dict.keys()

            if selected:
                # 全选
                redis_conn.sadd('selected_%s' % user.id, *sku_ids)
            else:
                # 取消全选
                redis_conn.srem('selected_%s' % user.id, *sku_ids)

            return JsonResponse({'code': '0',
                                 'errmsg': '全选购物车成功'})
        else:
            # 用户已登录，操作cookie购物车
            # 用户未登录，操作 cookie 购物车
            cookie_cart = request.COOKIES.get('carts')
            response = JsonResponse({'code': 0, 'errmsg': '全选购物车成功'})
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

                for sku_id in cart_dict.keys():
                    cart_dict[sku_id]['selected'] = selected

                cart_data = base64.b64encode(pickle.dumps(cart_dict)).decode()

                response.set_cookie('carts', cart_data)

            return response