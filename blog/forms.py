from django import forms

from .models import Meta


class LoginForm(forms.Form):
    username = forms.SlugField(max_length=32, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用户名',}))
    password = forms.CharField(max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '密码',}))


class CommentCreateForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control',}))
    id = forms.IntegerField(initial=0, widget=forms.TextInput(attrs={'style': 'display: none;'}))


class RegisterForm(forms.Form):
    username = forms.SlugField(max_length=32, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    url = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    nickname = forms.CharField(max_length=32, widget=forms.TextInput(attrs={'class': 'form-control'}))
