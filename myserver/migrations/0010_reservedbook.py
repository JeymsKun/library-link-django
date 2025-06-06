# Generated by Django 5.2.1 on 2025-05-18 18:03

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myDjangoAdmin', '0014_libraryuser_otp_code_libraryuser_otp_expiry_and_more'),
        ('myserver', '0009_remove_borrowedbook_return_due'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReservedBook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reserved_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reserved_instances', to='myDjangoAdmin.book')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reserved_books', to='myDjangoAdmin.libraryuser')),
            ],
            options={
                'ordering': ['-reserved_at'],
                'unique_together': {('user', 'book')},
            },
        ),
    ]
