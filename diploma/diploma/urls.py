"""orders URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from backend.views import (
    SignUpView,
    RequestForChangePasswordView,
    ChangePasswordView,
    LoginView,
    PartnerPriceApiUpdate,
    AccountDetails,
    CategoryView,
    ShopView,
    CustomAuthToken,
    ProductInfoView,
    ProductInfoForUserView,
    OrderView,
    BasketTemplateView,
    PartnerOrderView,
    OrderUproveTemplateView,
    OrderPayedView,
    OrderTemplateView
)
from django.urls import path, include
from backend.views import HomepageView, AccountDetails
from data.outload_data import PartnerPriceFileUpdate

urlpatterns = [
    path('', HomepageView.as_view(), name='homepage'),
    path('admin/', admin.site.urls),
    path('activate/<slug:uidb64>/token=<slug:token>/', ChangePasswordView.as_view(), name='activate'),
    path('user/signup/', SignUpView.as_view(), name="signup_user"),
    path('user/password_change/', RequestForChangePasswordView.as_view(), name='user_password_change'),
    path('user/get_token/', CustomAuthToken.as_view(), name="info_token"),
    path('user/login/', LoginView.as_view(), name='login_user'),
    path('user/details', AccountDetails.as_view(), name='user_details'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('api/v1/products', ProductInfoView.as_view(), name='products'),
    path('user/products', ProductInfoForUserView.as_view(), name='products_user'),
    path('user/basket', BasketTemplateView.as_view(), name='user_basket'),
    path('user/orders', OrderTemplateView.as_view(), name='user_orders'),
    path('user/basket/uprove', OrderUproveTemplateView.as_view(), name='basket/uprove'),
    path('order/payed/<slug:uidb64>/token=<slug:token>/order=<slug:order>', OrderPayedView.as_view(), name='order_payed'),
    path('api/v1/partner/update', PartnerPriceApiUpdate.as_view(), name='partner_update_products'),
    path('api/v1/partner/orders', PartnerOrderView.as_view(), name='partner_orders'),
    path('api/v1/partner/file_update', PartnerPriceFileUpdate.as_view(), name='partner_update_products_file'),
    path('api/v1/user/order_data', OrderView.as_view(), name='order'),
    path('', include('django.contrib.auth.urls')),
]
