from django import forms
from django.conf import settings

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

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("is_anonymous"):
            cleaned["name"] = ""
            cleaned["email"] = ""
        else:
            if not cleaned.get("name"):
                self.add_error("name", "Name is required unless anonymous.")
            if not cleaned.get("email"):
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
