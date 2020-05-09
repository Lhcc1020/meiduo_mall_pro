from django.core.mail import send_mail
from django.conf import settings
import logging
logger = logging.getLogger('django')
from celery_tasks.main import celery_app
import os
from goods.models import SKU
from django.conf import settings
from django.template import loader
from celery_tasks.main import celery_app
from goods.utils import get_categories, get_goods_and_spec


# 定义一个发送函数, 发送 email:
@celery_app.task(name='send_verify_email')
def send_verify_email(to_email, verify_url):

      # 标题
    subject = "美多商城邮箱验证"
      # 发送内容:
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)


      # 进行发送
    result = send_mail(subject,
               "",
               settings.EMAIL_FROM,
               [to_email],
               html_message=html_message)

    return result


# 定义一个生成静态化页面的函数, 该函数需要用装饰器装饰:
@celery_app.task(name='generate_static_sku_detail_html')
def generate_static_sku_detail_html(sku_id):
    """
    生成静态商品详情页面
    :param sku_id: 商品id值
    """
    # 商品分类菜单
    dict = get_categories()

    goods, specs, sku = get_goods_and_spec(sku_id)

    # 渲染模板，生成静态html文件
    context = {
        'categories': dict,
        'goods': goods,
        'specs': specs,
        'sku': sku
    }

    # 加载 loader 的 get_template 函数, 获取对应的 detail 模板
    template = loader.get_template('detail.html')
    # 拿到模板, 将上面添加好的数据渲染进去.
    html_text = template.render(context)
    # 拼接模板要生成文件的位置:
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'goods/'+str(sku_id)+'.html')
    # 写入
    with open(file_path, 'w') as f:
        f.write(html_text)