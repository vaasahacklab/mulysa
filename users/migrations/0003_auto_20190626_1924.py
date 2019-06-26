# Generated by Django 2.2.2 on 2019-06-26 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20190618_1737'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='wants_access_rights',
        ),
        migrations.AddField(
            model_name='customuser',
            name='membership_plan',
            field=models.CharField(choices=[('MO', 'Membership only'), ('AR', 'Member with access rights')], default='AR', help_text='Access right grants 24/7 access and costs more than regular membership', max_length=2, verbose_name='Membership plan'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='municipality',
            field=models.CharField(max_length=255, verbose_name='Municipality / City'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='nick',
            field=models.CharField(help_text='IRC / Matrix nick or callsign', max_length=255, verbose_name='Nick'),
        ),
    ]
