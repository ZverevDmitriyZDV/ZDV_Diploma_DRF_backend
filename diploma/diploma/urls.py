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
    ProductInfoForUserView
)
from django.urls import path, include
from backend.views import HomepageView, AccountDetails
from data.outload_data import PartnerPriceFileUpdate

urlpatterns = [
    path('', HomepageView.as_view(), name='homepage'),
    path('admin/', admin.site.urls),
    path('activate/<slug:uidb64>/token=<slug:token>/', ChangePasswordView.as_view(), name='activate'),
    path('user/signup/', SignUpView.as_view(), name="signup"),
    path('user/password_change/', RequestForChangePasswordView.as_view(), name='password_change'),
    path('user/get_token/', CustomAuthToken.as_view(), name="info"),
    path('user/login/', LoginView.as_view(), name='login'),
    path('user/details', AccountDetails.as_view(), name='user-details'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductInfoView.as_view(), name='products'),
    path('user/products', ProductInfoForUserView.as_view(), name='products-user'),
    path('api/v1/partner/update', PartnerPriceApiUpdate.as_view(), name='update'),
    path('api/v1/partner/file_update', PartnerPriceFileUpdate.as_view(), name='file_update'),
    path('', include('django.contrib.auth.urls')),
]
