import logging
from django.contrib.auth.views import LoginView
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import CreateView, TemplateView
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from requests import get
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from yaml import load as load_yaml, Loader
from django.db.models import Q, Sum, F
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from backend.forms import (
    CustomUserCreationForm,
    InfoForPasswordChangeForm,
    PasswordChangeForm,
    ClientCardForm,
    AccountInfoForm,
    PasswordChangeForm,
    ShopForm
)
from backend.serializers import (
    ShopSerializer,
    ClientCardSerializer,
    UserSerializer,
    CategorySerializer,
    ProductParameterSerializer,
    ProductInfoSerializer,
    OrderItemSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ShopSerializerForCustomer,
    ProductGetSerializer,
    ProductSerializer,
    ProductGetProductSerializer,
    ShopNameSerializer,
    ProductGetShopSerializer,
    PartnerOrderSerializer,
    OrderSerializerTemplate
)
from backend.models import (
    Shop,
    ProductInfo,
    Product,
    Order,
    OrderItem,
    CustomUser,
    Category,
    Parameter,
    ProductParameter,
    ClientCard
)
from rest_framework.authtoken.models import Token
from backend.tasks import send_auto_message
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.throttling import UserRateThrottle

# logger = logging.getLogger(__name__)


class HomepageView(TemplateView):
    """
    Класс главной старницы
    """
    template_name = 'homepage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Главная'
        return context


class CustomAuthToken(ObtainAuthToken):
    """
    класс определения токен-ключа
    при запросе проверяет тип пользователя, если магазон, то выдает/создает токен пользователю

    """
    throttle_classes = [UserRateThrottle]
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, 'signup.html')

        if self.request.user.type == 'client':
            return JsonResponse({'Status': False, 'Error': 'Need to be a distributor and have shop for token request'},
                                status=403)

        token, created = Token.objects.get_or_create(user=self.request.user)
        if created:
            message = f''' для API доступа используйте токкен {token.key}'''
            mail_subject = f"Приветсвуем Shop, Ниже Token для API"
            send_auto_message.delay(mail_subject=mail_subject, message=message, to_email=self.request.user.email)
        return Response({
            'token': token.key,
            'email': self.request.user.email
        })


class SignUpView(CreateView):
    throttle_classes = [UserRateThrottle]
    """
    класс для создания новых пользователей, по custom шаблону
    пользователь при регистарции может указать свой тип самостоятельно, от этого зависит получит ли он токе-ключ или нет на почту

    """
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("homepage")
    template_name = 'signup.html'

    def post(self, request, *args, **kwargs):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            token, created = Token.objects.get_or_create(user=user)
            message = f'''Для доступа на сайт вам понадобится ваш НИК: {form.data.get('username')} и Пароль: {form.data.get('password1')}'''
            if form.data.get("type") == "distributor":
                message += f''' для API доступа используйте токкен {token.key}'''

            subject_message = 'Добро пожаловать на сайте'
            send_auto_message.delay(mail_subject=subject_message, message=message, to_email=form.data.get("email"))

            return redirect("homepage")
        else:
            return render(request, self.template_name, {"form": form})


class LoginView(LoginView):
    """
    Класс позваоляет логиниться пользователям
    """
    template_name = 'login.html'
    success_url = reverse_lazy("homepage")
    throttle_classes = [UserRateThrottle]

    # Redirect from login page in case user already authenticated and loggedin
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('homepage')
        return self.render_to_response(self.get_context_data())


def send_email_passord(user, request):
    '''

    :param user: переадаем пользователя из БД, пользователь должен существовать
    :param request:
    :return: отправленное письмо
    '''
    user = user
    to_email = user.email
    vid = urlsafe_base64_encode(force_bytes(user.pk))
    token, created = Token.objects.get_or_create(user=user)
    current_site = get_current_site(request)
    message = render_to_string('active_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': vid,
        'token': token.key,
    })
    mail_subject = 'Activate your blog account.'
    send_auto_message.delay(mail_subject=mail_subject, message=message, to_email=to_email)


class RequestForChangePasswordView(APIView):
    throttle_classes = [UserRateThrottle]
    """
    класс отправляет сообщение с сылкой на изменение пароля
    определяем пользователя ,
    если авторизован - ссылка на смену пароля отправлятся сразу,
    если нет - заполняется запрос через форму
    формируется письмо и отправлятся на адрес пользователя, если он прошел аутенфикацию.
    Если просто хочет заменить пароль без авторизации, то формируется письмо, через поиск в БД пользователяЮ
     если найден пользователь по ключевым полям, то отправляем отправляемся письмо с сылкой на изменение пароля
    """
    template_name = 'password_reset_form.html'

    def get(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            form = InfoForPasswordChangeForm(request.POST)
            return render(request, self.template_name, {"form": form})

        send_email_passord(self.request.user, request)
        return JsonResponse({'Status': "Check your email"}, status=200)

    def post(self, request, *args, **kwargs):
        form = InfoForPasswordChangeForm(request.POST)
        serializer = UserSerializer(form.data)
        serializer_data = serializer.data
        try:
            user = CustomUser.objects.get(
                last_name=serializer_data.get('last_name'),
                first_name=serializer_data.get('first_name'),
                username=serializer_data.get('username'),
                email=serializer_data.get('email'),
            )
        except:
            return render(request, self.template_name, {"form": form})
        send_email_passord(user, request)
        return JsonResponse({'Status': "Check your email"}, status=200)


class ChangePasswordView(APIView):
    throttle_classes = [UserRateThrottle]
    """
    класс переписывает в БД пароль пользователя через доступ по токен-ключу
    через форму делаем валидацию пароля, в классе сверяем соответствие
    после успешного изменения пароля? токен, если пользователь имеет тип покупатель, стирается
    """
    authentication_classes = [TokenAuthentication]
    template_name = 'password_reset_form_confirm.html'

    def get(self, request, *args, **kwargs):
        form = PasswordChangeForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        token = kwargs.get('token')
        need_user = Token.objects.get(key=token)
        user = CustomUser.objects.get(id=need_user.user.id)
        form = PasswordChangeForm(request.POST)
        if form.data.get("password1") != form.data.get("password2"):
            return render(request, self.template_name, {"form": form})
        user.set_password(form.data.get("password1"))
        user.save()
        if user.type != "distributor":
            need_user.delete()
        return JsonResponse({'Status': True, 'Comment': f'''Password Changed to {form.data.get("password1")}'''})


class AccountDetails(CreateView):
    """
    Класс для работы c данными пользователя
    допустимо менять адрессуню карточку имя / фамилию / тип пользователя
    """

    form_class = AccountInfoForm
    success_url = reverse_lazy("homepage")
    template_name = 'edit.html'

    # получить данные и вставить в форму если есть
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '')
        form = AccountInfoForm(instance=request.user)
        try:
            client_card = ClientCard.objects.get(user_id=request.user.id)
            form2 = ClientCardForm(instance=client_card)
        except:
            form2 = ClientCardForm()
        return render(request, self.template_name, {"form": form, "form2": form2})

    # внести изменения / внести данные если пусто для редактирования
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '')
        form = AccountInfoForm(request.POST)
        if form.is_valid():
            user_needed = CustomUser.objects.get(id=self.request.user.id)
            user_serializer = UserSerializer(user_needed, data=form.data, partial=True)
            if user_serializer.is_valid():
                user_serializer.save()

        form2 = ClientCardForm(request.POST)
        if form2.is_valid():
            valid_data = form2.data
            valid_data._mutable = True
            valid_data.update({'user': self.request.user.id})
            try:
                client_card = ClientCard.objects.get(user_id=self.request.user.id)
                serializer = ClientCardSerializer(client_card, data=valid_data, partial=True)
            except:
                serializer = ClientCardSerializer(data=valid_data)
            if serializer.is_valid():
                serializer.save()
            return redirect("homepage")
        else:
            return render(request, self.template_name, {"form": form, "form2": form2})


class PartnerPriceApiUpdate(APIView):
    throttle_classes = [UserRateThrottle]
    """
    Класс для обновления прайса от поставщика
    обновление через ссылку на файл прайса
    Идет проверка пользователя на сохдание магазина
    Если Магазин не принадлежит пользователю, то будет ошибка
    """

    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'distributor':
            return Response({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return Response({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                try:
                    shop = Shop.objects.get(name=data['shop'], user=request.user.id)
                except:
                    return Response({'Status': False, 'Error': 'Магазина не существует'}, status=403)

                if shop is None:
                    return Response({'Status': False, 'Error': 'за пользователем не зарегестрирован магазин'},
                                    status=403)

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

        return Response({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class CategoryView(ListAPIView):
    throttle_classes = [UserRateThrottle]
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(APIView):
    throttle_classes = [UserRateThrottle]
    """
    Класс для редактирования данных Магазина если пользователь магазин
    Если пользователь - клиент, то выдаст список вагазинов по запросу
    """
    template_name = 'shop.html'

    def get(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('homepage')
        if request.user.type != 'client':
            try:
                shop = Shop.objects.get(user_id=self.request.user.id)
                form = ShopForm(instance=shop)
            except:
                form = ShopForm()
            return render(request, self.template_name, {"form": form})
        queryset = Shop.objects.filter(state=True)
        serializer = ShopSerializerForCustomer(queryset, many=True)
        if serializer.is_valid:
            return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, 'signup.html')
        if request.user.type == 'client':
            return JsonResponse({'Status': False, 'Errors': 'Редактировать Магазин могут только пользователи'})
        form = ShopForm(request.POST)
        if form.is_valid():
            valid_data = form.data
            valid_data._mutable = True
            valid_data.update({'user': self.request.user.id})
            try:
                shop = Shop.objects.get(user=self.request.user.id)
                serializer = ShopSerializer(shop, data=valid_data, partial=True)
            except:
                serializer = ShopSerializer(data=valid_data)
            if serializer.is_valid():
                serializer.save()
            return redirect("homepage")
        else:
            return render(request, self.template_name, {"form": form})


class ProductInfoViewSet(viewsets.ModelViewSet):
    queryset = ProductInfo.objects.all().select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

    serializer_class = ProductGetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


##### ViewSet замена ProductInfoView : APIWiew
# class ProductInfoView(APIView):
#     """
#     Класс для поиска всех товаров товаров
#     или с использованием фильтров
#     http://127.0.0.1:8000/products?category_id=224&shop_id=3
#     """
#
#     def get(self, request, *args, **kwargs):
#
#         query = Q(shop__state=True)
#         shop_id = request.query_params.get('shop_id')
#         category_id = request.query_params.get('category_id')
#
#         if shop_id:
#             query = query & Q(shop_id=shop_id)
#
#         if category_id:
#             query = query & Q(product__category_id=category_id)
#
#         # фильтруем и отбрасываем дуликаты
#         queryset = ProductInfo.objects.filter(
#             query).select_related(
#             'shop', 'product__category').prefetch_related(
#             'product_parameters__parameter').distinct()
#
#         serializer = ProductGetSerializer(queryset, many=True)
#
#         return Response(serializer.data)


class ProductInfoForUserView(TemplateView):
    template_name = 'product_list.html'
    '''
    мотод для передачи данных на рендер страницы
    get выдает отформатированные данные по ID товара.
    post - получаем request из формы, передает количество на заказ и данные ProductInfo
    '''

    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        order_item, _ = Order.objects.get_or_create(user_id=user_id, status='in_process')
        products_query = Product.objects.all()
        data_list = []
        for product in products_query:
            shop_query = ProductInfo.objects.filter(
                product=product.id
            ).prefetch_related('shop', 'product_parameters__parameter')
            serializer_shop = ProductGetShopSerializer(shop_query, many=True)
            shop_list = []
            info_list = []
            for shop in serializer_shop.data:
                shop_name = shop.get("shop")["name"]
                shop_id = shop.get("shop")["id"]
                product_info = shop.get("product_parameters")
                shop_list.append(
                    dict(
                        id=shop_id,
                        name=shop_name
                    )
                )
                query = Q(product_id=shop.get("id")) & Q(order_id=order_item.id) & Q(shop_id=shop_id)
                ordered_items = OrderItem.objects.filter(query).distinct()
                if ordered_items.exists():
                    ordered_items_serializer = OrderItemSerializer(ordered_items, many=True)
                    qty_ordered = ordered_items_serializer.data[0]['quantity']
                else:
                    qty_ordered = 0
                product_info_dict = dict(
                    shop=shop_name,
                    info=product_info,
                    price=shop.get("price"),
                    price_rrc=shop.get("price_rrc"),
                    quantity=shop.get("quantity"),
                    shop_id=shop_id,
                    product_info_id=shop.get("id"),
                    ordered_items=qty_ordered
                )
                info_list.append(product_info_dict)
            data = dict(
                id=product.id,
                name=product.name,
                category=product.category,
                shops=shop_list,
                info=info_list
            )
            data_list.append(data)
        return render(request, self.template_name, {"context": data_list})

    def post(self, request, *args, **kwargs):
        user_id = request.user.id
        shop_id = request.POST.get("shop_id")
        qty = request.POST.get("qty")
        product_info_id = request.POST.get("product_info_id")
        order_item, _ = Order.objects.get_or_create(user_id=user_id, status='in_process')

        try:
            order_exist = OrderItem.objects.get(order_id=order_item.id,
                                                product_id=product_info_id)
            order_exist.quantity = qty
            order_exist.save()
        except:
            new_order_item = OrderItem.objects.create(order_id=order_item.id,
                                                      product_id=product_info_id,
                                                      quantity=qty,
                                                      shop_id=shop_id)
        return self.get(request, *args, **kwargs)


class OrderView(APIView):
    throttle_classes = [UserRateThrottle]
    '''класс для получения данных по истории заказе API по авторизованному клиенту'''

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        order = Order.objects.filter(
            user=request.user.id).prefetch_related(
            'order_items__product__product__category',
            'order_items__product__product_parameters__parameter').select_related('user').annotate(
            total_sum=Sum(F('order_items__quantity') * F('order_items__product__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class OrderPayedView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        order = Order.objects.get(id=kwargs.get("order"))
        order.status = 'paid'
        order.save()
        return Response({"Status": "PAYED"})


class OrderTemplateView(TemplateView):
    '''шаблон выдачи информации по заказу'''
    template_name = 'order_list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        order = Order.objects.filter(
            user=request.user.id).exclude(status="in_process").prefetch_related(
            'order_items__product__product__category',
            'order_items__product__product_parameters__parameter').select_related('user').annotate(
            total_sum=Sum(F('order_items__quantity') * F('order_items__product__price'))).distinct()

        serializer = OrderSerializerTemplate(order, many=True)
        return render(request, self.template_name, {"context": serializer.data})


class OrderUproveTemplateView(OrderView):
    '''класс для подтверждения заказа'''

    def post(self, request, *args, **kwargs):
        order_id = request.POST.get('order_id')
        price = request.POST.get('price')
        user = request.user
        to_email = user.email
        vid = urlsafe_base64_encode(force_bytes(user.pk))
        token, created = Token.objects.get_or_create(user=user)
        current_site = get_current_site(request)
        message = render_to_string('order_confirmed.html', {
            'user': user,
            'order': order_id,
            'price': price,
            'domain': current_site.domain,
            'uid': vid,
            'token': token.key,
        })

        mail_subject = 'Your Order '

        send_auto_message.delay(mail_subject=mail_subject, message=message, to_email=to_email)

        return Response({'Status': "Письмо отправлено"})


class BasketTemplateView(TemplateView):
    '''класс для обработки элементов корзины'''
    template_name = 'basket_list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        order = Order.objects.filter(
            user=request.user.id, status="in_process").prefetch_related(
            'order_items__product__product__category',
            'order_items__product__product_parameters__parameter').select_related('user').annotate(
            total_sum=Sum(F('order_items__quantity') * F('order_items__product__price'))).distinct()
        serializer = OrderSerializer(order, many=True)

        if serializer.data[0]['total_sum'] is None:
            return redirect('products_user')

        return render(request, self.template_name, {"context": serializer.data[0]})

    def post(self, request, *args, **kwargs):
        method_iner = request.POST.get("method")
        if method_iner == "Удалить   заказ":
            order_id = request.POST.get("order_id")
            order = Order.objects.get(id=order_id)
            order.delete()
            return redirect('products_user')

        order_item_id = request.POST.get("order_item_id")
        qty = request.POST.get("qty")
        need_item = OrderItem.objects.get(id=order_item_id)

        method_iner = 'удалить' if int(qty) == 0 else method_iner
        if method_iner == 'изменить':
            need_item.quantity = qty
            need_item.save()
        elif method_iner == 'удалить':
            need_item.delete()
        return self.get(request)


class PartnerOrderView(APIView):
    """
    Класс для поиска всех товаров в заказе для конкретного магазина
    с использованием фильтра по номеру заказа
    http://127.0.0.1:8000/api/v1/partner/orders?order=2?status="paid"
    """

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        if request.user.type != "distributor":
            return JsonResponse({'Status': False, 'Error': 'Log in as shop required'}, status=403)

        order_id = request.query_params.get('order')
        status = request.query_params.get('status')
        shop_order = Shop.objects.get(user=request.user.id)
        query = Q(shop_id=shop_order.id)
        if order_id:
            query = query & Q(order_id=order_id)
        if status:
            query = query & Q(order__status=status)

        orders = OrderItem.objects.filter(query).prefetch_related(
            'order__user'
        ).select_related(
            'order'
        )

        serializer = PartnerOrderSerializer(orders, many=True)
        return Response(serializer.data)
