from django.http import HttpResponse
from django.shortcuts import render
import random
# Create your views here.
from django.views import View
from django_redis import get_redis_connection
import logging
from meiduo_mall_demo.libs.captcha.captcha import captcha
from django import http
from meiduo_mall_demo.libs.yuntongxun.sms import CCP


class ImgCheckView(View):
    '''图片验证码校验'''

    def get(self, request, uuid):
        '''生成图形验证码'''
        text, image = captcha.generate_captcha()
        # 链接redis
        redis_cot = get_redis_connection('verify_code')
        # 保存验证数据到redis
        redis_cot.setex('pic_%s' % uuid, 300, text)
        # 返回图片给前端
        return HttpResponse(image,
                            content_type='img/jpg')


logger = logging.getLogger('django')


class MobileCheck(View):
    '''短信验证码校验'''

    def get(self, request, mobile):
        # 接受参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 校验参数
        if not all([image_code_client, uuid]):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少参数'})

        # 创建连接redis对象
        redis_conn = get_redis_connection('verify_code')

        # 提取图形验证码
        image_code_server = redis_conn.get('pic_%s' % uuid)
        # 判断图形验证码是否存在或者过期
        if image_code_server is None:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '图形验证码失效'})
        # 验证后删除，避免恶意使用验证码
        try:
            redis_conn.delete('pic_%s' % uuid)
        except Exception as e:
            logger.error(e)

        # 比对验证码信息
        # 解码
        image_code_server = image_code_server.decode()
        # 比对小写字母
        if image_code_server.lower() != image_code_client.lower():
            return http.JsonResponse({'code': 400,
                                      'errmsg': '图形验证码错误'})

        # 随机生成六位短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)

        # 保存生成的验证码，并设置有效期
        redis_conn.setex('sms_%s' % mobile,
                         300,
                         sms_code)

        # 发送手机验证码
        # 短信模板
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        # 返回响应结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': '短信发送成功'})
