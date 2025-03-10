import datetime as dt

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

import rest_framework_filters as filters

from . import models


class ServiceSubscriptionCountFilter(admin.SimpleListFilter):
    title = _("Service Subscription Count")
    parameter_name = "service_subscription_count"

    def lookups(self, request, model_admin):
        # Defines filter options in the dropdown
        return (
            ("0", _("0 Subscriptions")),
            ("1", _("1 Subscription")),
            ("2", _("2 Subscriptions")),
            ("more_than_2", _("More than 2 Subscriptions")),
        )

    def queryset(self, request, queryset):
        # Filters the queryset based on the selected option
        if self.value() == "0":
            return queryset.annotate(
                num_subscriptions=Count("servicesubscription")
            ).filter(num_subscriptions=0)
        elif self.value() == "1":
            return queryset.annotate(
                num_subscriptions=Count("servicesubscription")
            ).filter(num_subscriptions=1)
        elif self.value() == "2":
            return queryset.annotate(
                num_subscriptions=Count("servicesubscription")
            ).filter(num_subscriptions=2)
        elif self.value() == "more_than_2":
            return queryset.annotate(
                num_subscriptions=Count("servicesubscription")
            ).filter(num_subscriptions__gt=2)
        return queryset


class PredefAgeListFilter(admin.SimpleListFilter):
    title = _("Age")
    parameter_name = "age"

    def lookups(self, request, model_admin):
        """
        Few predefined filters
        """
        return (
            ("under18", _("Under 18 years")),
            ("over18", _("Over 18 years")),
            ("under30", _("Under 30 years")),
            ("20to50", _("20 to 60")),
            ("over63", _("Over 63 years")),
        )

    def queryset(self, request, queryset):
        """
        filter the queryset
        """
        today = dt.date.today()

        if self.value() == "under18":
            return queryset.filter(birthday__gte=self._add_years(today, -18))
        if self.value() == "over18":
            return queryset.filter(birthday__lte=self._add_years(today, -18))
        if self.value() == "under30":
            return queryset.filter(birthday__gte=self._add_years(today, -30))
        if self.value() == "20to50":
            return queryset.filter(birthday__lte=self._add_years(today, -20)).filter(
                birthday__gte=self._add_years(today, -60)
            )
        if self.value() == "over63":
            return queryset.filter(birthday__lte=self._add_years(today, -63))

    def _add_years(self, dt, years):
        try:
            dt = dt.replace(year=dt.year + years)
        except ValueError:
            dt = dt.replace(year=dt.year + years, day=dt.day - 1)
        return dt


class MarkedForDeletionFilter(admin.SimpleListFilter):
    title = _("Marked for deletion")
    parameter_name = "marked_for_deletion_on__isnull"

    def lookups(self, request, model_admin):
        """
        Few predefined filters
        """
        return (
            ("false", _("Marked for deletion")),
            ("true", _("NOT Marked for deletion")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "true":
            return queryset.filter(marked_for_deletion_on__isnull=True)
        elif value == "false":
            return queryset.filter(marked_for_deletion_on__isnull=False)

        return queryset


class UserFilter(filters.FilterSet):
    class Meta:
        model = models.CustomUser
        fields = {
            "email": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "first_name": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "last_name": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "phone": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "is_active": ["isnull", "exact"],
            "is_staff": ["isnull", "exact"],
            "created": [
                "exact",
                "lt",
                "gt",
                "gte",
                "lte",
                "range",
                "date",
                "year",
                "iso_year",
                "month",
                "day",
                "week",
                "week_day",
                "quarter",
                "isnull",
            ],
            "last_modified": [
                "exact",
                "lt",
                "gt",
                "gte",
                "lte",
                "range",
                "date",
                "year",
                "iso_year",
                "month",
                "day",
                "week",
                "week_day",
                "quarter",
                "isnull",
            ],
            "marked_for_deletion_on": [
                "exact",
                "lt",
                "gt",
                "gte",
                "lte",
                "range",
                "date",
                "year",
                "iso_year",
                "month",
                "day",
                "week",
                "week_day",
                "quarter",
                "isnull",
            ],
            "birthday": [
                "exact",
                "lt",
                "gt",
                "gte",
                "lte",
                "range",
                "year",
                "iso_year",
                "month",
                "day",
                "week",
                "week_day",
                "quarter",
                "isnull",
            ],
            "nick": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "municipality": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
        }
