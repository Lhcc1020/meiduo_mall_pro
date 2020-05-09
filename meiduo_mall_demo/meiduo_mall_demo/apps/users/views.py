from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django import http
from django.views import View
from django_redis import get_redis_connection
import json
from celery_tasks.email.tasks import send_verify_email
from goods.models import SKU
from meiduo_mall_demo.utils.view import LoginRequird
from users.models import User, Address
import re
from django.contrib.auth import login, authenticate, logout
import logging

logger = logging.getLogger('django')


class UsernameCountView(View):
    '''判断用户名是否已经使用'''

    def get(self, request, username):
        '''判断是否重复'''
        try:
            # 判断数据库中用户名个数
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '访问数据库失败'})
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count': count})


class UsermobilPhone(View):
    '''手机号判断'''

    def get(self, request, mobile):
        '''检验手机号是否重复'''
        try:
            # 判断手机号个数
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '数据查询错误'})
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count': count})


class Regeist(View):
    '''用户注册，保存信息'''

    def post(self, request):
        '''接收用户信息参数'''
        dic = json.loads(request.body.decode())
        username = dic.get('username')
        password = dic.get('password')
        password2 = dic.get('password2')
        mobile = dic.get('mobile')
        sms_code = dic.get('sms_code')
        allow = dic.get('allow')

        # 检查整体数据是否完整
        if not all([username, password, password2, mobile, sms_code, allow]):
            return http.JsonResponse({'code': 400, 'errmsg': '参数错误，缺少必要参数'})

        # 分步校验
        # 校验用户名
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.JsonResponse({'code': 400, 'errmsg': '用户名格式错误'})
        # 密码格式校验
        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return http.JsonResponse({'code': 400, 'errmsg': '密码格式错误'})

        # 比对密码
        if password2 != password:
            return http.JsonResponse({'code': 400, 'errmsg': '两次输入不相同'})

        # 电话校验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'cede': 400, 'errmsg': '电话号码输入有误'})

        # 协议确认
        if allow != True:
            return http.JsonResponse({'code': 400, 'errmsg': '协议未勾选'})

        # 验证码校验
        # 链接redis
        redis_conn = get_redis_connection('verify_code')

        # 取出需要比对的值
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 判断该值是否存在
        if not sms_code_server:
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码过期'})

        # 校验验证码
        if sms_code_server.decode() != sms_code:
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码有误'})

        # 保存用户信息到数据库
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': '存入数据库出错'})

        # 状态保持
        login(request, user)
        # 返回Json
        return http.JsonResponse({'code': 0, 'errmsg': 'ok'})


class Login(View):
    """登录函数"""

    def post(self, request):
        '''实现用户名登录'''

        # 接受参数
        dir = json.loads(request.body.decode())
        username = dir.get('username')
        password = dir.get('password')
        remembered = dir.get('remembered')

        # 总体检验
        if not all([username, password]):
            return http.JsonResponse({'code': 400, 'errmsg': '关键参数错误'})

        # 校验用户名和密码
        user = authenticate(username=username, password=password)

        # 判断检验结果
        if user is None:
            return http.JsonResponse({'code': 400, 'errmsg': '用户名或者密码错误'})

        # 状态保持
        login(request, user)

        # 判断是否记住状态
        if remembered != True:
            # 浏览器关闭退出登录
            request.session.set_expiry(0)
        else:
            # 保持登录，默认记录两周
            request.session.set_expiry(None)

        # 定义相应对象
        response = http.JsonResponse({'code': 0, 'errmsg': 'ok'})

        # 设置cookie ，时限14天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

        # 返回Json
        return response


class LogOut(View):
    '''创建一个登出接口'''

    def delete(self, request):
        # 使用logout登出
        logout(request)

        # 创建返回对象
        response = http.JsonResponse({'code': 0, 'errmsg': 'ok'})

        # 清除cookie
        response.delete_cookie('username')

        # 返回响应
        return response


class UserInfo(LoginRequird, View):
    # 用户中心
    def get(self, request):
        '''只有登录用户才能进入该类视图'''

        info_data = {
            'username': request.user.username,
            "mobile": request.user.mobile,
            "email": request.user.email,
            "email_active": request.user.email_active
        }

        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok',
                                  'info_data': info_data})


class AddEmail(View):
    '''添加邮箱信息'''

    def put(self, request):
        # 接受参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return http.JsonResponse({'code': 400, 'errmsg': '缺少邮箱参数'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '邮箱参数有误'})
        # 添加邮箱信息到数据库
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                      'errmsg': '保存邮箱到数据库出错'})

        # 发送验证邮件到当前用户邮箱
        # 将验证链接生成
        verify_url = request.user.make_token_value()
        # 发送验证邮件
        send_verify_email.delay(email, verify_url)

        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok'})


class UserEmailActive(View):
    '''邮箱激活验证'''

    def put(self, request):

        # 接受参数
        token = request.GET.get('token')

        # 检验参数
        if not token:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少token'})

        # token存在
        # 调用函数，提取user信息
        user = User.check_email(token)
        if not user:
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'token无效'})

        try:
            # user获取正常，修改email_active,保存
            user.email_active = True
            user.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                      'errmsg': '邮箱激活失败'})

            # 返回邮箱验证结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': 'ok'})


class Adderss_Add(View):
    '''新增地址'''

    def post(self, request):

        # 获取地址个数
        try:
            count = Address.objects.filter(user=request.user,
                                           is_deleted=False).count()

        except Exception as e:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '获取地址出错'})

        # 判断是否超过地址上限：最多20个
        if count >= 20:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '超过地址数量上限'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '必要参数缺失'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'mobile错误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({'code': 400,
                                          'errmsg': 'tel错误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.JsonResponse({'code': 400,
                                          'errmsg': 'email错误'})

        # 保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400,
                                      'errmsg': '新增地址失败'})

        # 新增地址成功，将新增的地址返回前段显示
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': '增加地址成功',
                                  'address': address_dict})


class Address_View(View):
    """用户收货地址"""

    def get(self, request):
        """提供地址管理界面
        """
        # 获取所有的地址:
        addresses = Address.objects.filter(user=request.user,
                                           is_deleted=False)

        # 创建空的列表
        address_dict_list = []
        # 遍历
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }

            # 将默认地址移动到最前面
            default_address = request.user.default_address
            if default_address.id == address.id:
                # 查询集 addresses 没有 insert 方法
                address_dict_list.insert(0, address_dict)
            else:
                address_dict_list.append(address_dict)

        default_id = request.user.default_address_id

        return JsonResponse({'code': 0,
                           'errmsg': 'ok',
                           'addresses': address_dict_list,
                           'default_address_id': default_id})


class ChangeAddress(View):
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""

        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': 'mobile错误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': 'tel错误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': 'email错误'})

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': '更新地址成功',
                                  'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        return JsonResponse({'code': 0,
                             'errmsg': '删除地址成功'})


class DefaultAddress(View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return JsonResponse({'code': 0,
                             'errmsg': '设置默认地址成功'})


class SetAddressTitle(View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return JsonResponse({'code': 0,
                             'errmsg': '设置地址标题成功'})


class ChangePassword(LoginRequird, View):
    """修改密码"""

    def put(self, request):
        """实现修改密码逻辑"""
        # 接收参数
        dict = json.loads(request.body.decode())
        old_password = dict.get('old_password')
        new_password = dict.get('new_password')
        new_password2 = dict.get('new_password2')

        # 校验参数
        if not all([old_password, new_password, new_password2]):
           return JsonResponse({'code':400,
                                     'errmsg':'缺少必传参数'})


        result = request.user.check_password(old_password)

        if not result:
            return JsonResponse({'code':400,
                                      'errmsg':'原始密码不正确'})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({'code':400,
                                      'errmsg':'密码最少8位,最长20位'})

        if new_password != new_password2:
            return JsonResponse({'code':400,
                                      'errmsg':'两次输入密码不一致'})

        # 修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '修改密码失败'})

        # 清理状态保持信息
        logout(request)

        response = JsonResponse({'code': 0,
                                 'errmsg': 'ok'})

        response.delete_cookie('username')

        # # 响应密码修改结果：重定向到登录界面
        return response

class UserBrowseHistory(View):
    """用户浏览记录"""

    def post(self, request):
        """保存用户浏览记录"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 校验参数:
        try:
            SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.HttpResponseForbidden('sku不存在')

        # 保存用户浏览数据
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        user_id = request.user.id

        # 先去重: 这里给 0 代表去除所有的 sku_id
        pl.lrem('history_%s' % user_id, 0, sku_id)
        # 再存储
        pl.lpush('history_%s' % user_id, sku_id)
        # 最后截取: 界面有限, 只保留 5 个
        pl.ltrim('history_%s' % user_id, 0, 4)
        # 执行管道
        pl.execute()

        # 响应结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': 'OK'})

    def get(self, request):
        """获取用户浏览记录"""
        # 获取Redis存储的sku_id列表信息
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % request.user.id, 0, -1)

        # 根据sku_ids列表数据，查询出商品sku信息
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image_url,
                'price': sku.price
            })

        return http.JsonResponse({'code': 0,
                                  'errmsg': 'OK',
                                  'skus': skus})