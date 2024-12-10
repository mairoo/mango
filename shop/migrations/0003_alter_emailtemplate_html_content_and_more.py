# Generated by Django 5.1.3 on 2024-12-10 04:04

import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_emailtemplate'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailtemplate',
            name='html_content',
            field=models.TextField(verbose_name='HTML 내용'),
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='subject',
            field=models.CharField(max_length=255, verbose_name='이메일 제목'),
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='template_name',
            field=models.CharField(max_length=255, unique=True, verbose_name='템플릿 이름'),
        ),
        migrations.AlterField(
            model_name='emailtemplate',
            name='text_content',
            field=models.TextField(verbose_name='텍스트 내용'),
        ),
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('cart_data', models.JSONField(blank=True, default=dict, verbose_name='cart data')),
                ('version', models.BigIntegerField(default=0, verbose_name='version')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'cart',
                'verbose_name_plural': 'carts',
            },
        ),
    ]