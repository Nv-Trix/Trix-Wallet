from django.dispatch import receiver
from django.db.models.signals import post_save,pre_save
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

from django.db import transaction

from .models import Account,Transfer,Withdraw,TransactionType
from notifications.models import Notification
from accounts.models import Profile

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from core import state

from core.api.utils import converCurrency
from notifications import status as notification_status

User = get_user_model()


# --------------------------------Django SIgnals------------------------------------------

@receiver(post_save, sender=User)
def createAccount(sender, instance,created, **kwargs):
    """ ## User post Save signal
    
        This signal is use to create the profile,token,and account of a ussr when it is created
    Args:
        sender (User): the User model
        instance (User): the instance of a User created
        created (bool): a boolean true if the object is been created other wise false
    """

    if created:
        # it means when the user is created
    
        if not Account.objects.select_related('user').filter(user=instance).exists():
            Account.objects.create(user=instance)
        if not Token.objects.filter(user=instance).exists():
            Token.objects.create(user=instance)
        if not Profile.objects.filter(user=instance):
            profile = Profile.objects.create(user=instance, dob=timezone.now().date())
        else:
            profile = Profile.objects.select_related('profile').get(user=instance)
        
        lang = profile.lang
        msg = ''

        if lang == 'FR':
            msg = f'Bienvenu sur {settings.APP_NAME}\nVotre code pin est [00000] et solde de votre compte est {profile.user.account.currency} {profile.user.account.balance}'
        elif lang == 'EN':
            msg = f'Welcome To {settings.APP_NAME} \nYour pin code is [00000] and account balance is {profile.user.account.currency} {profile.user.account.balance}'

        Notification.objects.create(user=profile.user, message=msg)


@receiver(pre_save,sender=Profile)
def passThroughProfile(sender,instance,*args,**kwargs):
    if instance.user is not None:
        current = instance
        previous = Profile.objects.filter(user=instance.user)
        if previous.exists():
            previous = previous.first()
            if current.lang != previous.lang:

                lang = instance.user.profile.lang

                if lang == 'FR':
                    msg = f'La langue de votre compte a ete changer de {previous.lang} a {instance.lang}'
                else:
                    msg = f'The language of your account have been changed from {previous.lang} to {instance.lang}'

                Notification.objects.create(user=instance.user, message=msg)

@receiver(pre_save, sender=Account)
def checkAccount(sender, instance, **kwargs):

    # If Instance/row is been created,then do nothing
    if instance.id is None:
        pass

    # Else if it is being modified

    else:
        current = instance
        previous = Account.objects.get(id=instance.id)

        # if the previous currency is not equal to the current currency

        if previous.display_currency != current.display_currency:
            # convert the account balance to the new currency
            

            lang = instance.user.profile.lang

            if lang == 'FR':
                msg = f'La monnaie de votre compte a ete changer de {previous.display_currency} a {instance.display_currency}'
            else:
                msg = f'The currency of your account have been changed from {previous.display_currency} to {instance.display_currency}'

            Notification.objects.create(user=instance.user, message=msg)

        if previous.pin_code != current.pin_code:
            lang = instance.user.profile.lang
            msg = ''
            if lang == 'FR':
                msg = f'Votre code pin a ete changer de {previous.pin_code} a {instance.pin_code}'
            else:
                msg = f'Your account pin code has been change successfully from  {previous.pin_code} to {instance.pin_code}'

            Notification.objects.create(user=instance.user, message=msg)


@receiver(pre_save, sender=Transfer)
def checkIfUserCanTransferMoney(sender, instance, **kwargs):
    
    if instance.id is None:
        sender_account = Account.objects.select_related(
            'user').get(id=instance.sender.id)
        balance = sender_account.balance
        reciever_account = Account.objects.select_related(
            'user').get(id=instance.reciever.id)

        amount = float(instance.amount)

        if sender_account.id == reciever_account.id:
            msg = ''
            if sender_account.user.profile.lang == 'FR':
                msg = 'Desoler ! vous ne pouvez pas vous envoyer de l\'argent!'
            elif sender_account.user.profile.lang == 'EN':
                msg = 'Sorry ! You can\'t send mney to your self!'

            Notification.objects.create(
                user=sender_account.user, message=msg, type=notification_status.NOTIFICATION_ALERT)
            Notification.objects.create(
                user=sender_account.user, message='Transfer could not be achieve successfully!', type="TRANSFER_REJECTED")

            instance.status = state.WITHDRAW_REJECTED

        else:

            if float(sender_account.balance) >= amount:
                with transaction.atomic():

                    if sender_account.is_agent:
                        charge = TransactionType.objects.select_related('transaction_type').filter(
                            name__icontains='deposit').first().transaction_type
                    else:
                        charge = TransactionType.objects.select_related('transaction_type').filter(
                            name__icontains='transfer').first().transaction_type

                    amount_charge = amount*charge.charge
                    amount_send = amount - amount_charge

                    sender_account.balance = balance - amount_send
                    sender_account.save()

                    new_amount = converCurrency(
                        sender_account.currency, reciever_account.currency, float(amount_send))

                    reciever_account.balance = float(
                        reciever_account.balance)+new_amount
                    reciever_account.save()

                    instance.currency = sender_account.currency

                    instance.charge = charge

            else:
                instance.currency = sender_account.currency
                instance.status = state.TRANSFER_REJECTED
                Notification.objects.create(user=sender_account.user, message="Your account balance is insufficent to perform the transaction. Please fill you account and retry later!\nCurrent account balance {}".format(
                    sender_account.get_balance()), type=notification_status.NOTIFCATION_WITHDRAW_REJECTED)
                
@receiver(post_save, sender=Transfer)
def sendNotificationsToAccounst(sender, instance, created, **kwargs):
    """
     ## Transfer ModelPost ave Signal for
     
    """

    if created:
        if instance.status == 'SUCCESSFULL':
            Notification.objects.create(user=instance.sender.user, message=instance.generateMessage(
                instance.sender.user.profile.lang)["sender_message"], type=notification_status.NOTIFICATION_TRANSFER_SUCCESSFULL)

            Notification.objects.create(user=instance.reciever.user, message=instance.generateMessage(
                instance.reciever.user.profile.lang)["reciever_message"], type=notification_status.NOTIFICATION_NORMAL)


@receiver(post_save,sender=Withdraw)
def accept_or_deny(sender,instance,created,**kwargs):
    """_summary_

    Args:
        sender (Withdraw): _description_
        instance (Withdraw): _description_
        created (boolean): _description_
    """    
    withdraw_from = Account.objects.select_related(
            'user').get(id=instance.withdraw_from.id)
    agent = Account.objects.select_related(
        'user').get(id=instance.agent.id)
    balance = withdraw_from.balance
    instance.currency = withdraw_from.currency


    amount = instance.amount

    if instance.state == state.WITHDRAW_CANCEL:

        sender_msg = ''
        receiver_msg = ''

        lang = withdraw_from.user.profile.lang
        lang1 = agent.user.profile.lang

        if lang == 'EN':
            sender_msg = f'The withdrawal of {instance.currency} {instance.amount} from your account {withdraw_from.account_number} by {agent.user.first_name} {agent.user.last_name} [{agent.user}] has been cancel'
        elif lang == 'FR':
            sender_msg = f'La demande de retrait de {instance.currency} {instance.amount} de votre compte {agent.account_number} par {agent.user.first_name} {agent.user.last_name} [{agent.user}] a ete annulez'

        if lang1 == 'EN':
            receiver_msg = f'The withdrawal of {instance.currency} {instance.amount} from the account {withdraw_from.account_number} {withdraw_from.user.first_name} {withdraw_from.user.last_name} [{withdraw_from.user}] has been cancel'
        elif lang1 == 'FR':
            receiver_msg = f'Le retrait de  {instance.currency} {instance.amount} du compte {withdraw_from.account_number} {withdraw_from.user.first_name} {withdraw_from.user.last_name} [{withdraw_from.user}] a ete annulez'

        Notification.objects.create(
            user=instance.withdraw_from.user,
            msg=sender_msg,
            type=notification_status.NOTIFICATION_WITHDRAW_CANCEL
        )

        Notification.objects.create(
            user=instance.agent.user,
            msg=receiver_msg,
            type=notification_status.NOTIFICATION_WITHDRAW_CANCEL
        )

    elif instance.state == state.WITHDRAW_ACCEPTED:

        if float(withdraw_from.balance) >= float(amount):
            with transaction.atomic():

                charge = TransactionType.objects.select_related('transaction_type').filter(
                    name__icontains='withdraw').first().transaction_type
                amount_charge = float(amount)*float(charge.charge)
                amount_to_withdraw = float(amount) - float(amount_charge)

                withdraw_from.balance = float(balance) - amount_to_withdraw
                withdraw_from.save()

                agent.balance = float(agent.balance) + amount_to_withdraw
                agent.save()

                instance.charge = charge

                instance.save()

        else:
            instance.status = state.WITHDRAW_REJECTED
            instance.save()

            Notification.objects.create(user=withdraw_from.user, message="Your account balance is insufficent to perform the transaction. Please fill you account and retry later!\nCurrent account balance {}".format(
                withdraw_from.get_balance()), type=notification_status.NOTIFCATION_WITHDRAW_REJECTED)


@receiver(pre_save, sender=Withdraw)
def checkIfUserCanWithdrawMoney(sender, instance, **kwargs):

    if instance.id is None:

        withdraw_from = Account.objects.select_related(
            'user').get(id=instance.withdraw_from.id)
        agent = Account.objects.select_related(
            'user').get(id=instance.agent.id)
        balance = withdraw_from.balance

        instance.currency = withdraw_from.currency

        amount = instance.amount

        if withdraw_from.id == agent.id:
            msg = ''
            if agent.user.profile.lang == 'FR':
                msg = 'Desoler ! vous ne pouvez pas vous retirez de l\'argent!'
            elif agent.user.profile.lang == 'EN':
                msg = 'Sorry ! You can\'t withdraw money from your self!'
            Notification.objects.create(
                user=agent.user, message=msg, type=notification_status.NOTIFICATION_ALERT)
        else:

            charge = TransactionType.objects.select_related('transaction_type').filter(
                    name__icontains='withdraw').first().transaction_type

            instance.charge = charge
            if float(withdraw_from.balance) >= float(amount):
                instance.status = state.WITHDRAW_PENDING
            else:

                instance.status = state.WITHDRAW_REJECTED

                Notification.objects.create(user=withdraw_from.user, message="Your account balance is insufficent to perform the transaction. Please fill you account and retry later!\nCurrent account balance {}".format(
                    withdraw_from.get_balance()), type=notification_status.NOTIFCATION_WITHDRAW_REJECTED)