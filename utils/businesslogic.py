import logging
from datetime import date, timedelta

from django.utils import translation
from django.utils.translation import gettext as _

from drfx import settings
from users.models import (
    BankTransaction,
    CustomInvoice,
    CustomUser,
    MemberService,
    ServiceSubscription,
)
from users.signals import application_approved, application_denied

logger = logging.getLogger(__name__)


class BusinessLogic:
    """
    Implements business logic for the membership services.

    Contains a set of static methods callable from outside and some
    mostly internal ones.
    """

    @staticmethod
    def new_transaction(transaction):
        """
        Called when a new transaction has been added into database
        """
        logger.debug(f"New transaction {transaction}")
        transaction_user = None
        if transaction.reference_number and transaction.reference_number > 0:
            try:
                # Figure out if a user can be mapped to transaction
                transaction_user = CustomUser.objects.get(
                    reference_number=transaction.reference_number
                )
                transaction.user = transaction_user
                transaction.save()
            except CustomUser.DoesNotExist:
                pass
        if transaction.user:
            translation.activate(transaction.user.language)
            transaction.user.log(
                _("Bank transaction of %(amount)s€ dated %(date)s")
                % {"amount": str(transaction.amount), "date": str(transaction.date)}
            )

    @staticmethod
    def update_all_users():
        """
        Can be called from anywhere. Updates user data for all users.
        """
        all_users = CustomUser.objects.all()
        for user in all_users:
            BusinessLogic.updateuser(user)

    @staticmethod
    def updateuser(user):
        """
        Updates the user's status based on the data in database. Can be called from outside.
        """
        # Check for custom invoices..
        invoices = CustomInvoice.objects.filter(
            user=user, payment_transaction__isnull=True
        )
        for invoice in invoices:
            try:
                transaction = BankTransaction.objects.get(
                    reference_number=invoice.reference_number, has_been_used=False
                )
                BusinessLogic._check_transaction_pays_custominvoice(transaction)
            except BankTransaction.DoesNotExist:
                pass

        # Now we check transactions done to user's default account
        defaultservice = MemberService.objects.get(id=settings.DEFAULT_ACCOUNT_SERVICE)
        servicesubscriptions = ServiceSubscription.objects.filter(
            user=user, service=defaultservice
        )

        # Update user's servicesubscription if it exists:
        if len(servicesubscriptions) == 1:
            for subscription in servicesubscriptions:
                logger.debug(f"Examining default subscription {subscription}")
                BusinessLogic._updatesubscription(
                    user, subscription, servicesubscriptions
                )
                BusinessLogic._check_servicesubscription_state(subscription)

    @staticmethod
    def reject_application(application):
        """
        Rejects a membership application and deletes the user
        """
        logger.debug(f"Rejecting app {application}")
        # TODO: Send mail and any other notifications to user?
        # Should delete the application
        application_denied.send(sender=application.__class__, instance=application)
        application.user.delete()

    @staticmethod
    def accept_application(application):
        """
        Accepts a membership application
        """
        logger.debug(f"Accepting app {application}")
        # TODO: Send mail and any other notifications to user?
        application_approved.send(sender=application.__class__, instance=application)
        user = application.user
        user.log(_("Accepted as member"))
        # Move user's subscriptions to overdue state
        for subscription in ServiceSubscription.objects.filter(user=user):
            subscription.state = ServiceSubscription.OVERDUE
            subscription.save()
            BusinessLogic._servicesubscription_state_changed(
                subscription, ServiceSubscription.SUSPENDED, subscription.state
            )

        application.delete()
        BusinessLogic.updateuser(user)

    # PRIVATE methods below - don't call these from outside (unless you know what you're doing!)

    @staticmethod
    def _check_servicesubscription_state(subscription):
        """
        Checks if the servicesubscription state needs to be changed due to paid_until changed.
        """
        # We do nothing if subscription is suspended
        if subscription.state == ServiceSubscription.SUSPENDED:
            return

        oldstate = subscription.state

        # Check if the service has been overdue and can be activated
        if (
            subscription.state == ServiceSubscription.OVERDUE
            and subscription.paid_until
            and subscription.paid_until > date.today()
        ):
            subscription.state = ServiceSubscription.ACTIVE
            subscription.save()
            BusinessLogic._servicesubscription_state_changed(
                subscription, oldstate, subscription.state
            )

        # Check if the service becomes overdue
        if (
            subscription.state == ServiceSubscription.ACTIVE
            and subscription.paid_until
            and subscription.paid_until < date.today()
        ):
            logger.debug(f"{subscription} payment overdue so changing state to OVERDUE")
            subscription.state = ServiceSubscription.OVERDUE
            subscription.save()
            BusinessLogic._servicesubscription_state_changed(
                subscription, oldstate, subscription.state
            )
        # TODO: Handle moving subscription from OVERDUE to SUSPENDED if enough time passes.

    @staticmethod
    def _servicesubscription_state_changed(subscription, oldstate, newstate):
        """
        This is called when service state changes.
        Can be used to trigger notifications or anything.
        """
        translation.activate(subscription.user.language)
        subscription.user.log(
            _("Service %(servicename)s state changed from %(oldstate)s to %(newstate)s")
            % {
                "servicename": subscription.service.name,
                "oldstate": oldstate,
                "newstate": newstate,
            }
        )

    @staticmethod
    def _check_transaction_pays_custominvoice(transaction):
        """
        Checks if given transaction pays any custom invoice
        """
        invoices = CustomInvoice.objects.filter(
            reference_number=transaction.reference_number,
            payment_transaction__isnull=True,
        )

        for invoice in invoices:
            if transaction.amount >= invoice.amount:
                try:
                    logger.debug(f"Transaction {transaction} pays invoice {invoice}")
                    subscription = ServiceSubscription.objects.get(
                        user=invoice.user, id=invoice.subscription.id
                    )
                    if not subscription.paid_until:
                        subscription.paid_until = transaction.date
                    subscription.paid_until = subscription.paid_until + timedelta(
                        days=invoice.days
                    )
                    subscription.last_payment = transaction
                    invoice.payment_transaction = transaction
                    transaction.has_been_used = True
                    transaction.user = invoice.user
                    transaction.save()
                    invoice.save()
                    subscription.save()
                    transaction.user.log(
                        _(
                            "Paid %(days)s days of %(name)s, ending at %(until)s with transaction %(transaction)s"
                            % {
                                "days": invoice.days,
                                "name": subscription.service.name,
                                "until": subscription.paid_until,
                                "transaction": transaction,
                            }
                        )
                    )
                    BusinessLogic._check_servicesubscription_state(subscription)
                except ServiceSubscription.DoesNotExist:
                    logger.debug(
                        "Transaction would pay for invoice but user has no servicesubscription??"
                    )
            else:
                logger.debug(
                    f"Transaction {transaction} insufficient for invoice {invoice}"
                )

    @staticmethod
    def _updatesubscription(user, subscription, servicesubscriptions):
        """
        Updates a single subscription status for given user (used by updateuser)
        """
        logger.debug(f"Updating {subscription} for {user}")
        translation.activate(user.language)

        # Suspended subscriptions need manual action so can be skipped
        if subscription.state == ServiceSubscription.SUSPENDED:
            logger.debug("Service is suspended - no action")
            return

        # Figure out other services that pay for this service
        services_that_pay_this = MemberService.objects.filter(
            pays_also_service=subscription.service
        )
        for service in services_that_pay_this:
            if BusinessLogic._user_is_subscribed_to(servicesubscriptions, service):
                logger.debug(
                    f"Service is paid by {service} which user is subscribed so skipping this service."
                )
                return

        # Check generic transactions that could pay for this service
        transactions = BankTransaction.objects.filter(
            user=user, has_been_used=False
        ).order_by("date")

        for transaction in transactions:
            if BusinessLogic._transaction_pays_service(
                transaction, subscription.service
            ):
                logger.debug(
                    f"Transaction is new and pays for service {subscription.service}"
                )
                BusinessLogic._service_paid_by_transaction(subscription, transaction)
            else:
                logger.debug(f"Transaction does not pay service {subscription.service}")

    @staticmethod
    def _transaction_pays_service(transaction, service):
        """
        Checks if given transaction pays the service. Returns boolean.
        """
        if service.cost_min and transaction.amount < service.cost_min:
            return False
        if not service.cost_min and transaction.amount < service.cost:
            return False
        return True

    @staticmethod
    def _user_is_subscribed_to(servicesubscriptions, service):
        """
        Returns True if user (whose servicesubscriptions is given) is subscribed to given service
        """
        for subscription in servicesubscriptions:
            if subscription.service == service:
                return True
        return False

    @staticmethod
    def _service_paid_by_transaction(servicesubscription, transaction):
        """
        Called if transaction actually pays for extra time on given service subscription
        """
        translation.activate(servicesubscription.user.language)

        # How many days to add to subscription's paid until
        days_to_add = timedelta(days=servicesubscription.service.days_per_payment)

        # First payment - initialize with payment date and add first time bonus days
        if not servicesubscription.paid_until:
            bonus_days = timedelta(
                days=servicesubscription.service.days_bonus_for_first
            )
            logger.debug(
                f"{servicesubscription} paid for first time, adding bonus of {bonus_days}"
            )
            days_to_add = days_to_add + bonus_days
            servicesubscription.paid_until = transaction.date

        # TODO Check maximum time that can be paid and limit payments to it.

        # Add days and mark this transaction to be the last payment
        servicesubscription.paid_until = servicesubscription.paid_until + days_to_add
        servicesubscription.last_payment = transaction
        servicesubscription.save()

        # Mark transaction as used
        transaction.has_been_used = True
        transaction.save()

        servicesubscription.user.log(
            _("%(servicename)s is now paid until %(until)s due to %(transaction)s")
            % {
                "servicename": str(servicesubscription),
                "until": str(servicesubscription.paid_until),
                "transaction": str(transaction),
            }
        )

        # Handle case where this service also pays for another service
        if servicesubscription.service.pays_also_service:
            # All subscription for current user paid by this service
            paid_servicesubscriptions = ServiceSubscription.objects.filter(
                user=servicesubscription.user,
                service=servicesubscription.service.pays_also_service,
            )
            for paid_servicesubscription in paid_servicesubscriptions:
                logger.debug(f"{servicesubscription} also pays for {paid_servicesubscription}")
                if paid_servicesubscription.state == ServiceSubscription.SUSPENDED:
                    logger.debug("Service is suspended - no action")
                else:
                    extra_days = timedelta(
                        days=paid_servicesubscription.service.days_per_payment
                    )
                    paid_servicesubscription.paid_until = transaction.date + extra_days
                    paid_servicesubscription.last_payment = transaction
                    paid_servicesubscription.save()
                    servicesubscription.user.log(
                        _(
                            "%(servicename)s is now paid until %(until)s due to %(anotherservicename)s was paid"
                        )
                        % {
                            "servicename": str(paid_servicesubscription),
                            "until": str(paid_servicesubscription.paid_until),
                            "anotherservicename": str(servicesubscription.service),
                        }
                    )

                    BusinessLogic._check_servicesubscription_state(
                        paid_servicesubscription
                    )
