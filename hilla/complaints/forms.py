from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Ticket, TicketComment, TicketRating

try:
    from django_recaptcha.fields import ReCaptchaField
    from django_recaptcha.widgets import ReCaptchaV2Checkbox
except Exception:
    ReCaptchaField = None
    ReCaptchaV2Checkbox = None


class TicketForm(forms.ModelForm):
    is_anonymous = forms.BooleanField(
        required=False,
        label="Submit anonymously",
        help_text="Your name and email will not be shown.",
    )

    if getattr(settings, "ENABLE_RECAPTCHA", False) and ReCaptchaField:
        captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    class Meta:
        model = Ticket
        fields = [
            "category",
            "type",
            "priority",
            "is_anonymous",
            "name",
            "email",
            "subject",
            "message",
        ]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_anonymous"):
            cleaned["name"] = ""
            cleaned["email"] = ""
        else:
            is_auth_user = bool(getattr(self.user, "is_authenticated", False))
            if not cleaned.get("name") and not is_auth_user:
                self.add_error("name", "Name is required unless anonymous.")
            if not cleaned.get("email") and not is_auth_user:
                self.add_error("email", "Email is required unless anonymous.")
        return cleaned


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ["author_name", "text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4}),
        }


class TicketRatingForm(forms.ModelForm):
    SCORE_CHOICES = [(i, str(i)) for i in range(1, 6)]
    score = forms.TypedChoiceField(choices=SCORE_CHOICES, coerce=int)

    class Meta:
        model = TicketRating
        fields = ["score", "rater_name", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3}),
        }


class AdminCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Passwords do not match.")
        return cleaned


class AvatarForm(forms.Form):
    avatar = forms.ImageField(required=True)


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
