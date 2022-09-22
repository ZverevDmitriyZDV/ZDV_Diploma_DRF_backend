from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.conf import settings


# This code is triggered whenever a new user has been created and saved to the database
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


USER_TYPE_CHOICES = (
    ('distributor', 'Магазин'),
    ('client', 'Покупатель'),
)

ORDER_CHOICES = (
    ('confirmed', 'подтвержден'),
    ('canceled', 'отменен'),
    ('in_process', 'в процессе выбора клиентом'),
    ('paid', 'оплачен'),
    ('assembly', 'в процессе сборки'),
    ('in delivery', 'передан в службу доставки'),
    ('in client', 'доставлен'),
)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=15, default='client')
    username = models.CharField(unique=True, max_length=150, verbose_name='Ник пользователя')
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Список пользователей"
        ordering = ('email',)



class Shop(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    url = models.URLField(max_length=200, blank=True, null=True)
    filename = models.CharField(max_length=100,blank=True, null=True)
    user = models.OneToOneField(CustomUser, verbose_name='Пользователь в базе', on_delete=models.CASCADE, blank=True,
                                null=True)
    state = models.BooleanField(verbose_name='Магазин принимает заказы', default=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Список магазинов'

    def __str__(self):
        return f"{self.name}: file for data: {self.filename}"


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    shops = models.ManyToManyField(Shop)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Список категорий'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 verbose_name='Категория', related_name='products')
    name = models.CharField(max_length=100, verbose_name='Название')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Список продуктов'

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Продукт', related_name='product_infos')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE,
                             verbose_name='Магазин', related_name='product_infos')
    name = models.CharField(max_length=100, verbose_name='Название')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    bp_number = models.PositiveIntegerField(verbose_name='Внутренний артикул')
    price = models.PositiveIntegerField(verbose_name='Стоимость')
    price_rrc = models.PositiveIntegerField(verbose_name='Стоимость без скидки')

    class Meta:
        verbose_name = "Информация о продукте"
        verbose_name_plural = 'Список продуктов'
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop', 'bp_number'], name='unique_product_info'),
        ]


class Parameter(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Список параметров'

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE,
                                     verbose_name='Информация по продукту', related_name='product_parameters')
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE,
                                  verbose_name='Параметр продукта', related_name='product_parameters')
    value = models.CharField(max_length=100, verbose_name='Значение')

    class Meta:
        verbose_name_plural = 'Список параметров'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameters'),
        ]


class ClientCard(models.Model):
    user = models.ForeignKey(CustomUser, verbose_name='Пользователь', related_name='contacts', blank=True,
                             on_delete=models.CASCADE)
    apt = models.CharField(max_length=70, verbose_name="апартаменты", blank=True)
    buildings = models.CharField(max_length=70, verbose_name="номер дома", blank=True)
    street = models.CharField(max_length=150, verbose_name="улица", blank=True)
    city = models.CharField(max_length=70, verbose_name="город")
    country = models.CharField(max_length=100, verbose_name="страна")
    postcode = models.PositiveIntegerField(verbose_name="почтовый индекс")
    mobile = models.CharField(max_length=20, verbose_name='Контактный номер телефона')

    class Meta:
        verbose_name = "Карточка  контактов клиента"
        verbose_name_plural = "Карточки клиентов"


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Пользователь', related_name='orders')
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=35, verbose_name='Статус заказа', choices=ORDER_CHOICES, default="in_process")

    class Meta:
        verbose_name = "Заказ"
        ordering = ("-dt",)
        verbose_name_plural = "Список заказов"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Заказ", related_name="order_items")
    product = models.ForeignKey(ProductInfo, on_delete=models.CASCADE, verbose_name="Инфо о продукте",
                                related_name="order_items")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name="Магазин", related_name="order_items")
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Список заказанных позиций"
        constraints = [
            models.UniqueConstraint(fields=['order_id', 'product'], name='unique_order_item'),

        ]
