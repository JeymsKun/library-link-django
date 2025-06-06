# Generated by Django 5.2.1 on 2025-05-18 17:17

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myDjangoAdmin', '0014_libraryuser_otp_code_libraryuser_otp_expiry_and_more'),
        ('myserver', '0007_bookingcart'),
    ]

    operations = [
        migrations.CreateModel(
            name='BorrowedBook',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('borrowed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('return_due', models.DateTimeField()),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrowed_instances', to='myDjangoAdmin.book')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrowed_books', to='myDjangoAdmin.libraryuser')),
            ],
            options={
                'ordering': ['-borrowed_at'],
                'unique_together': {('user', 'book')},
            },
        ),
    ]
