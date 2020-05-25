from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from goods.models import SKUImage
from meiduo_admin.serializers.image import ImageModelSerializer
from meiduo_admin.utils import PageNum

"""
- 开启Fdfs的tracker
- 开启Fdfs的storage
- 安装Fdfs的库（即提供给大家的Fdfs压缩包)

# 以下三步，我们在哪里写呢？？？
- 创建Fdfs客户端
- 上传图片二进制
- 获取上传结果，根据上传结果进行file_id的保存
"""

class ImageModelViewSet(ModelViewSet):

    queryset = SKUImage.objects.all()

    serializer_class = ImageModelSerializer

    #设置分页
    pagination_class = PageNum

    """
    当我们新增SKUImage的时候，会调用 CreateModelMixin 的create方法
    但是这个create方法，不能满足我们的需求
    我们的需求是：
    # - 创建Fdfs客户端
    # - 上传图片二进制
    # - 获取上传结果，根据上传结果进行file_id的保存
    """
    def create(self, request, *args, **kwargs):

        # sku, 图片
        # 1. 接收数据
        # POST
        sku_id = request.data.get('sku')
        # 2. 获取图片数据
        photo = request.FILES.get('image')
        # 3. 创建Fdfs客户端
        from fdfs_client.client import Fdfs_client
        client = Fdfs_client('meiduo_mall/utils/fastdfs/client.conf')
        # 4. 上传图片二进制
        # photo 是文件
        # photo.read() 读取文件的二进制数据
        result = client.upload_by_buffer(photo.read())
        """
        {
            'Group name': 'group1',
            'Remote file_id': 'group1/M00/00/00/wKhnnlxw_gmAcoWmAAEXU5wmjPs35.jpeg',
            'Status': 'Upload successed.',
            'Local file name': '/Users/meihao/Desktop/demo.jpeg',
            'Uploaded size': '69.00KB',
            'Storage IP': '172.16.238.128'
        }
        """
        # 5. 获取上传结果，根据上传结果进行file_id的保存
        if result['Status'] == 'Upload successed.':
            file_id = result['Remote file_id']
            # 6. 保存SKUImage
            new_skuimage = SKUImage.objects.create(
                sku_id=sku_id,
                image=file_id
            )
            # 前端就是根据 201 进行判断的
            return Response({
                'id':new_skuimage.id,
                'sku':sku_id,
                'image':new_skuimage.image.url
            },status=201)
            # 7. 返回响应

        return Response({'msg':'error'})


"""
我们想要实现图片上传
1. 先获取SKU列表
    把所有的SKU都查询出来
2. 通过Fdfs实现图片上传

"""
from rest_framework.generics import ListAPIView
from goods.models import SKU
from meiduo_admin.serializers.image import SimpleSKUModleSerializer
class SimpleSKUListAPIView(ListAPIView):

    queryset = SKU.objects.all()

    serializer_class = SimpleSKUModleSerializer