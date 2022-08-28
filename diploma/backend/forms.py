from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import ModelForm
from backend.models import CustomUser, ClientCard, Shop
from django.contrib.auth.password_validation import validate_password


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        # fields = "__all__"
        fields = ('first_name', 'last_name', 'email', 'username', "type")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        # fields = "__all__"
        fields = ('first_name', 'last_name', 'email', 'password', 'type', 'username')


class ClientCardForm(ModelForm):
    class Meta:
        model = ClientCard
        fields = ('city', 'street', 'country', 'postcode', 'buildings', 'apt', 'mobile')


class AccountInfoForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'type',)


class PasswordChangeForm(forms.Form):
    password1 = forms.CharField(label='Enter New Password',
                                widget=forms.PasswordInput)

    password2 = forms.CharField(label='Repeat password',
                                widget=forms.PasswordInput)

    def clean_password(self):
        password = self.cleaned_data['password1']
        validate_password(password)
        return password

    # --- check duplicate
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']


class InfoForPasswordChangeForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'username')
        error_messages = {
            'first_name': {'required': ''},
            'last_name': {'required': '',
                          },
            'email': {
                'hepl_texts': '',
                'required': '',
                'unique': '',

            },
            'username': {'required': '',
                         'unique': ''},

        }
    # first_name = forms.CharField(max_length=100,error_messages = {'required': "something..."})
    # last_name = forms.CharField(max_length=100,error_messages = {'required': "something..."})
    # email = forms.EmailField(error_messages = {'required': "something..."})
    # username = forms.CharField(max_length=100,error_messages = {'required': "something..."})


class ShopForm(ModelForm):
    class Meta:
        model = Shop
        fields = ('name', 'url', 'filename','state')


# class ProductForm()