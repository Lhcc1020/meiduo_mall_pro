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
from celery_tasks.sms.tasks import ccp_send_sms_code


class ImgCheckView(View):
    '''返回图形验证码'''

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

        # 创建连接redis对象
        redis_conn = get_redis_connection('verify_code')
        # 先查询是否有上次发送时存入的检测数据是否在redis中存在
        send_flag= redis_conn.get('send_flag%s' % mobile)
        # 如果存在，返回提示
        if send_flag:
            return http.JsonResponse({'cede': 400,
                                      'errmsg': '短信申请过于频繁'})

        #redis中没有，开始接受参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 校验参数
        if not all([image_code_client, uuid]):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少参数'})



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
        print('验证码是：%s' % image_code_server.lower())
        # 比对小写字母
        if image_code_server.lower() != image_code_client.lower():
            print('输入验证码错误', image_code_client)
            return http.JsonResponse({'code': 400,
                                      'errmsg': '图形验证码错误'})

        # 随机生成六位短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        print('验证码是：', sms_code)
        logger.info(sms_code)

        # 创建redis管道
        pl = redis_conn.pipeline()

        # 保存生成的验证码，并设置有效期
        # redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        # 用管道保存验证码
        pl.setex('sms_%s' % mobile, 300, sms_code)

        # 发送验证码前向redis存一个检测数据，设置时间
        # redis_conn.setex('send_flag%s' % mobile, 60, 1)
        # 用管道发送检测数据
        pl.setex('send_flag%s' % mobile, 60, 1)

        # 调用管道
        pl.execute()

        # 发送手机验证码
        # 短信模板
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)
        # ccp_send_sms_code.delay(mobile, sms_code)

        # 返回响应结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': '短信发送成功'})
