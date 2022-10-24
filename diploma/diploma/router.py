from backend.views import ProductInfoViewSet
from rest_framework.routers import DefaultRouter
from backend import views

object_list = ProductInfoViewSet.as_view({
    'get': 'list'
})
object_detail = ProductInfoViewSet.as_view({
    'get': 'retrive'
})

router_viewset = DefaultRouter()
router_viewset.register(r'products', views.ProductInfoViewSet, basename='product')
