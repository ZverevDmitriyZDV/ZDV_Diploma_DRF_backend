import yaml
from yaml.loader import SafeLoader
from rest_framework.authentication import TokenAuthentication
from backend.models import (
    Shop,
    ProductInfo,
    Product,
    Category,
    Parameter,
    ProductParameter,
    CustomUser
)
from rest_framework.views import APIView
from rest_framework.response import Response
import os



class PartnerPriceFileUpdate(APIView):
    """
    Класс для обновления прайса от поставщикаc
    Только если есть файл прайса в папке data
    Только если пользователь зарегестрировал за собой Магазин

    POST / api / v1 / partner / file_update

    {
        "token": "76b06cbb9092619efc7fe9f08bbad327ea36a888",
        "filename": "shop1.yaml"
    }
    "все изменения внесены или созданы"

    {
        "token": "76b06cbb9092619efc7fe9f08bbad327ea36a888",
        "filename": "shop2.yaml"
    }
     'Магазина не существует'




    """

    authentication_classes = [TokenAuthentication]



    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)
        if request.user.type != 'distributor':
            return Response({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        file_name = request.data.get('filename')
        basedir = os.path.abspath(os.getcwd())
        with open(os.path.join(basedir, "data", file_name), encoding="utf-8") as file:
            data = yaml.load(file, Loader=SafeLoader)
        try:
            shop = Shop.objects.get(name=data['shop'], user=request.user.id)
        except:
            return Response({'Status': False, 'Error': 'Магазина не существует'}, status=403)

        if shop is None:
            return Response({'Status': False, 'Error': 'за пользователем не зарегестрирован магазин'}, status=403)
        for category in data['categories']:
            category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
            category_object.shops.add(shop.id)
            category_object.save()
        ProductInfo.objects.filter(shop=shop.id).delete()
        for item in data['goods']:
            product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

            product_info = ProductInfo.objects.create(product_id=product.id,
                                                      shop_id=shop.id,
                                                      name=item['model'],
                                                      quantity=item['quantity'],
                                                      bp_number=item['id'],
                                                      price=item['price'],
                                                      price_rrc=item['price_rrc'],

                                                      )
            for name, value in item['parameters'].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(product_info_id=product_info.id,
                                                parameter_id=parameter_object.id,
                                                value=value)

        return Response({'Status': "все изменения внесены или созданы"})
