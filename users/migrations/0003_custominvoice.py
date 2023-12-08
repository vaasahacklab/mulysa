# Generated by Django 3.0.2 on 2020-01-12 20:53

from drfx import config
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_auto_20200111_2016"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomInvoice",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "days",
                    models.IntegerField(
                        help_text="For example value 14 with access right service pays two weeks of access.",
                        verbose_name="How many days of service this invoice pays",
                    ),
                ),
                (
                    "reference_number",
                    models.BigIntegerField(
                        blank=True,
                        help_text="Reference number is set by transaction sender and must match this.",
                        null=True,
                        unique=True,
                        verbose_name="Reference number for paying invoice",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Minimum amount of money to satisfy this invoice.",
                        max_digits=6,
                        verbose_name="Amount",
                    ),
                ),
                (
                    "payment_transaction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="users.BankTransaction",
                    ),
                ),
                (
                    "subscription",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="users.ServiceSubscription",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=config.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
