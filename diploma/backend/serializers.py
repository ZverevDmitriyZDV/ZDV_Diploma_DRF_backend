from rest_framework import serializers

from backend.models import ClientCard, CustomUser, Shop, Category, Product, ProductParameter, ProductInfo, OrderItem, \
    Order


class ClientCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientCard
        fields = ('id', 'apt', 'buildings', 'street', 'city', 'country', 'postcode', 'mobile', 'user')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ClientCardSerializer(read_only=True, many=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'type', 'contacts')
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class ShopSerializerForCustomer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'url')
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'filename', 'user', 'state')
        read_only_fields = ('id',)


class ShopNameSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField()

    class Meta:
        model = Shop
        fields = ('name',)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductGetProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value',)


class ProductGetSerializer(serializers.ModelSerializer):
    product = ProductGetProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)
    shop = ShopNameSerializer(read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'name', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters',)
        read_only_fields = ('id',)


class ProductGetShopSerializer(ProductGetProductSerializer):
    shop = ShopSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ('shop','product_parameters','quantity', 'price', 'price_rrc')
        read_only_fields = ('id',)


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'name', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters',)
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'quantity', 'order',)
        read_only_fields = ('id',)
        extra_kwargs = {
            'order': {'write_only': True}
        }


class OrderItemCreateSerializer(OrderItemSerializer):
    product = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemCreateSerializer(read_only=True, many=True)
    total_sum = serializers.IntegerField()
    contact = ClientCardSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'status', 'dt', 'total_sum', 'contact',)
        read_only_fields = ('id',)
