# Generated by Django 2.2.2 on 2019-06-18 06:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_auto_20190617_2312'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField()),
                ('edit_time', models.DateTimeField()),
                ('author_ip', models.CharField(max_length=64)),
                ('status', models.CharField(max_length=16)),
                ('text', models.TextField()),
                ('author_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.User')),
                ('content_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blog.Content')),
                ('parent_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='blog.Comment')),
            ],
        ),
    ]
