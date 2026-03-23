from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm[User]):
    email = forms.EmailField(required=True, help_text="Email is required.")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit: bool = True) -> User:
        user = super().save(commit)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
