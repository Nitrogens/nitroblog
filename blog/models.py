from django.db import models


class User(models.Model):
    username = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=256)
    mail = models.CharField(max_length=200, unique=True)
    url = models.CharField(max_length=200)
    nickname = models.CharField(max_length=32, unique=True)
    create_time = models.DateTimeField()
    last_login_time = models.DateTimeField()
    group = models.CharField(max_length=32)


class Content(models.Model):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, unique=True)
    create_time = models.DateTimeField()
    edit_time = models.DateTimeField()
    summary = models.TextField()
    text = models.TextField()
    priority_id = models.IntegerField()
    author_id = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=16)


class Comment(models.Model):
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE)
    create_time = models.DateTimeField()
    edit_time = models.DateTimeField()
    author_id = models.ForeignKey(User, on_delete=models.CASCADE)
    author_ip = models.CharField(max_length=64)
    status = models.CharField(max_length=16)
    text = models.TextField()
    parent_id = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)


class Meta(models.Model):
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, unique=True)
    type = models.CharField(max_length=32)
    description = models.TextField()
    priority_id = models.IntegerField()


class Link(models.Model):
    name = models.CharField(max_length=200)
    url = models.CharField(max_length=200)


class Setting(models.Model):
    name = models.CharField(max_length=32)
    value = models.TextField()


class Relationship(models.Model):
    content_id = models.ForeignKey(Content, on_delete=models.CASCADE)
    meta_id = models.ForeignKey(Meta, on_delete=models.CASCADE)
