import mailchimp_transactional as MailchimpTransactional
from mailchimp_transactional.api_client import ApiClientError
import os


def run():
  mailchimp_trans_key = os.getenv("MAILCHIMP_TRANS_KEY")
  try:
    mailchimp = MailchimpTransactional.Client(mailchimp_trans_key)
    response = mailchimp.users.ping()
    print('API called successfully: {}'.format(response))
  except ApiClientError as error:
    print(mailchimp_trans_key)
    print('An exception occurred: {}'.format(error.text))

run()