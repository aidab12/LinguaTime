from django.contrib.auth import authenticate
from django.contrib.auth.forms import UsernameField
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms import Form, CharField, ModelForm, EmailField, PasswordInput, CheckboxSelectMultiple, EmailInput, \
    HiddenInput

from apps.models import Interpreter, Client


class LoginForm(Form):
    """Форма для входа пользователей."""
    email = EmailField(
        required=True,
        widget=EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address'
        }
    )
    password = CharField(
        max_length=128,
        required=True,
        widget=PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        }),
        error_messages={
            'required': 'Password is required'
        }
    )
    user_type = CharField(widget=HiddenInput())


    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        user_type = cleaned_data.get('user_type')

        if not email or not password:
            raise ValidationError("Email and password are required")

        user = authenticate(email=email, password=password)

        if user is None:
            raise ValidationError("Invalid email or password")


        if user_type == 'client':
            try:
                user.client
            except ObjectDoesNotExist:
                raise ValidationError("This account is not a client.")
        elif user_type == 'interpreter':
            try:
                user.interpreter
            except ObjectDoesNotExist:
                raise ValidationError("This account is not an interpreter.")
        else:
            raise ValidationError("Unknown user type.")

        self.user = user
        return cleaned_data


class RegisterClientModelForm(ModelForm):
    """Форма для регистрации клиентов"""
    password = CharField(
        max_length=128,
        widget=PasswordInput(attrs={'placeholder': 'Enter password', 'autocomplete': 'new-password'}),
        error_messages={'required': 'Password is required'}
    )
    confirm_password = CharField(
        max_length=128,
        widget=PasswordInput(attrs={'placeholder': 'Confirm password', 'autocomplete': 'new-password'}),
        error_messages={'required': 'Please confirm your password'}
    )

    class Meta:
        model = Client
        fields = ('first_name', 'last_name', 'phone', 'email')
        field_classes = {"phone": UsernameField}

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Client.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and Client.objects.filter(phone=phone).exists():
            raise ValidationError("Phone already exists")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords don't match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class RegisterInterpreterModelForm(ModelForm):
    """Форма для регистрации переводчиков"""
    password = CharField(max_length=128,widget=PasswordInput())
    confirm_password = CharField(max_length=128, widget=PasswordInput())

    class Meta:
        model = Interpreter
        fields = (
            'first_name',
            'last_name',
            'phone',
            'email',
            'password',
            'gender',
            'city',
            'is_ready_for_trips',
            'language',
            'translation_type',

        )
        widgets = {
            'password': PasswordInput(),
            'language': CheckboxSelectMultiple(),
            'translation_type': CheckboxSelectMultiple(),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and self.Meta.model.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and self.Meta.model.objects.filter(phone=phone).exists():
            raise ValidationError("Phone already exists")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords don't match")

        if not cleaned_data.get('language'):
            raise ValidationError('Please select at least one language')

        if self.instance._state.adding:
            if not cleaned_data.get('translation_type'):
                raise ValidationError('Plase select at least one translation type')

        return cleaned_data

    def save(self, commit=True):
        interpreter = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            interpreter.set_password(password)
        if commit:
            interpreter.save()
            self.save_m2m()

        return interpreter

# class ProfileChangePasswordModelForm(ModelForm):
#     old_password = CharField(max_length=128, required=True)
#     confirm_password = CharField(max_length=128, required=True)
#
#     class Meta:
#         model = User
#         fields = ['password']
#
#     def __init__(self, data=None, files=None, auto_id="id_%s", prefix=None, initial=None, error_class=ErrorList,
#                  label_suffix=None, empty_permitted=False, instance=None, use_required_attribute=None, renderer=None,
#                  request=None):
#         self.request = request
#         super().__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance,
#                          use_required_attribute, renderer)
#
#     def clean(self):
#         _data = super().clean()
#         user = self.request.user
#
#         old_password = _data.pop('old_password')
#         password = _data.get('password')
#         confirm_password = _data.pop('confirm_password')
#
#         if password != confirm_password or not user.check_password(old_password):
#             raise ValidationError("Passwords don't match")
#
#         user.set_password(password)
#         user.save(update_fields=['password'])
#         update_session_auth_hash(self.request, user)
#         return _data
