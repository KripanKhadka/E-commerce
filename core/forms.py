from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator

from .models import UserProfile

User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True, label="First name")
    last_name = forms.CharField(max_length=50, required=True, label="Last name")
    email = forms.EmailField(required=True)
    phone = forms.CharField(
        max_length=20,
        required=True,
        label="Phone number",
        validators=[RegexValidator(r"^(?:\+977[- ]?)?9\d{9}$", "Enter a valid Nepal mobile number, e.g. 98XXXXXXXX.")],
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Username"
        self.fields["username"].help_text = "Use 3–30 letters, numbers or @/./+/-/_ characters."
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm password"
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
            field.widget.attrs.setdefault("autocomplete", "off")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.full_name = user.get_full_name().strip()
            profile.phone = self.cleaned_data["phone"]
            profile.save(update_fields=["full_name", "phone"])
        return user


class AccountForm(forms.Form):
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(
        max_length=20, required=True,
        validators=[RegexValidator(r"^(?:\+977[- ]?)?9\d{9}$", "Enter a valid Nepal mobile number, e.g. 98XXXXXXXX.")],
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        profile = getattr(user, "userprofile", None) if user else None
        if user and not args:
            self.initial.update({
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": profile.phone if profile else "",
            })
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        qs = User.objects.filter(email__iexact=email).exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError("That email is already used by another account.")
        return email

    def save(self):
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["first_name", "last_name", "email"])
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.full_name = self.user.get_full_name().strip()
        profile.phone = self.cleaned_data["phone"]
        profile.save(update_fields=["full_name", "phone"])
        return self.user


class CheckoutForm(forms.Form):
    street_address = forms.CharField(required=False)
    apartment_address = forms.CharField(required=False)
    zip = forms.CharField(required=False)


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
    }))


class RefundForm(forms.Form):
    email = forms.EmailField()
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))


class PaymentForm(forms.Form):
    stripeToken = forms.CharField(required=False)
    save = forms.BooleanField(required=False)
    use_default = forms.BooleanField(required=False)
