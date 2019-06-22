from django import forms

from blog.models import Meta


class LoginForm(forms.Form):
    username = forms.CharField(max_length=32, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用户名',}))
    password = forms.CharField(max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '密码',}))


class PersonalInformationForm(forms.Form):
    email = forms.CharField(label="Email", max_length=200, widget=forms.TextInput(attrs={'class': 'form-control',}))
    url = forms.CharField(label="个人主页", max_length=200, widget=forms.TextInput(attrs={'class': 'form-control',}))
    nickname = forms.CharField(label="昵称", max_length=32, widget=forms.TextInput(attrs={'class': 'form-control',}))


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control',}))
    new_password = forms.CharField(max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control',}))
    new_password_confirm = forms.CharField(max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control',}))


class ArticleFilterForm(forms.Form):
    keyword = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '关键字',}))
    choice_list = [(0, '所有分类')]
    category_list = Meta.objects.filter(type="category")
    for category in category_list:
        choice_list.append((int(category.id), category.name))
    category = forms.ChoiceField(choices=choice_list, widget=forms.Select(attrs={'class': 'custom-select'}))


class ArticleCreateForm(forms.Form):
    title = forms.CharField(label='标题', max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    slug = forms.SlugField(label='标识符', max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    summary = forms.CharField(label='摘要', widget=forms.Textarea(attrs={'class': 'form-control'}))
    text = forms.CharField(label='文章内容', widget=forms.Textarea(attrs={'class': 'form-control'}))

    category_choice_list = []
    category_list = Meta.objects.filter(type="category")
    for category in category_list:
        category_choice_list.append((int(category.id), category.name))
    category = forms.MultipleChoiceField(choices=category_choice_list, label='分类',
                                         widget=forms.SelectMultiple(attrs={'class': 'custom-select', 'size': '10'}),
                                         required=False)

    tag_choice_list = []
    tag_list = Meta.objects.filter(type="tag")
    for tag in tag_list:
        tag_choice_list.append((int(tag.id), tag.name))
    tag = forms.MultipleChoiceField(choices=tag_choice_list, label='标签',
                                    widget=forms.SelectMultiple(attrs={'class': 'custom-select', 'size': '10'}),
                                    required=False)


class PageCreateForm(forms.Form):
    title = forms.CharField(label='标题', max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    slug = forms.SlugField(label='标识符', max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    summary = forms.CharField(label='摘要', widget=forms.Textarea(attrs={'class': 'form-control'}))
    text = forms.CharField(label='内容', widget=forms.Textarea(attrs={'class': 'form-control'}))
    priority_id = forms.IntegerField(label='优先级', widget=forms.TextInput(attrs={'class': 'form-control'}))
