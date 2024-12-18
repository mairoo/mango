# Generated by Django 5.1.3 on 2024-11-30 14:31

import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('template_name', models.CharField(help_text='이메일 템플릿의 고유 식별자로 사용됩니다.', max_length=255, unique=True, verbose_name='템플릿 이름')),
                ('html_content', models.TextField(help_text='이메일의 HTML 버전 템플릿입니다.', verbose_name='HTML 내용')),
                ('text_content', models.TextField(help_text='이메일의 텍스트 버전 템플릿입니다.', verbose_name='텍스트 내용')),
                ('subject', models.CharField(help_text='이메일의 제목 템플릿입니다.', max_length=255, verbose_name='이메일 제목')),
            ],
            options={
                'verbose_name': '이메일 템플릿',
                'verbose_name_plural': '이메일 템플릿',
                'ordering': ['-created'],
            },
        ),
    ]
