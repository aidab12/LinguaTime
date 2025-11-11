from django.contrib.auth import authenticate
from django.contrib.auth.forms import UsernameField, UserCreationForm
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.forms import Form, CharField, ModelForm, EmailField, PasswordInput, CheckboxSelectMultiple, EmailInput

from apps.models import User, Interpreter


class LoginForm(Form):
    """
    Форма для входа пользователей.
    Использует email вместо username.
    """
    email = EmailField(required=True, widget=EmailInput(attrs={'class': 'form-control','placeholder': 'your@email.com'}))
    password = CharField(max_length=128, required=True)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        try:
            user =

        if user is None:
            raise ValidationError("Incorrect email or password")

        self.user = user
        return cleaned_data


class CustomClientCreationForm(UserCreationForm):
    phone = CharField()
    first_name = CharField()
    last_name = CharField()
    email = EmailField()

    class Meta:
        model = User
        fields = ('phone', 'first_name', 'last_name', 'email')
        field_classes = {"phone": UsernameField}


class RegisterInterpreterModelForm(ModelForm):
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

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        return first_name.title()

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

    def save(self, commit = True):
        interpreter = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            interpreter.password = make_password(password)
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
