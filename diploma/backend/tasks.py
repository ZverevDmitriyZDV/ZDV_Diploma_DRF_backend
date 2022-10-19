from django.core.mail import EmailMessage
from time import sleep
from celery import shared_task


@shared_task()
def send_auto_message(mail_subject, message, to_email):
    """Sends an email """
    sleep(20)  # Simulate expensive operation(s) that freeze Django
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()
