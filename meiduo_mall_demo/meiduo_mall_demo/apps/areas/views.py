from django.shortcuts import render
from django.views import View
from areas.models import Area
from django import http
from django.core.cache import cache



class AreasProvince(View):
    '''省级地区获取'''

    def get(self, request):

        # 查询缓存里是否含有省级信息
        provinces_list = cache.get('province_list')

        if not provinces_list:
            try:
            # 1.查询省级信息
                province_lis = Area.objects.filter(parent__isnull=True)

                # 2.整理省级数据
                provinces_list = []
                for province in province_lis:
                    provinces_list.append({'id':province.id,
                                           'name': province.name})
                # 添加省级信息到缓存
                cache.set('provinces_list', provinces_list, 3600)

            except Exception as e:
                return http.JsonResponse({'code': 400, 'errmsg': '省级查询错误'})

        # 3.返回整理好的省级数据
        return http.JsonResponse({'code': 0, 'errmsg': 'Ok', 'province_list':provinces_list})



class SubAreasView(View):
    '''市和区级查询'''

    def get(self, request, pk):
        # 首先判断是否有缓存
        sub_data = cache.get('sub_area_' + pk)

        if not sub_data:
            # 1.查询市/区级数据
            try:
                sub_model_list = Area.objects.filter(parent=pk)
                # 查询其父级
                parent_model = Area.objects.get(id=pk)


                # 获取市/区信息到列表
                sub_list = []
                for sub_model in sub_model_list:
                    sub_list.append({'id': sub_model.id, 'name': sub_model.name})

                sub_data = {
                    'id': parent_model.id,
                    'name': parent_model.name,
                    'subs': sub_list
                }

                # 获取的市区列表添加到缓存
                cache.set('sub_area_' + pk, sub_data, 3600)

            except Exception as e:
                return http.JsonResponse({'code': 400, 'errmsg': '市/区查询错误'})

        # 返回响应
        return http.JsonResponse({'code': 0,
                                  'errmsg': 'OK',
                                  'sub_data': sub_data})