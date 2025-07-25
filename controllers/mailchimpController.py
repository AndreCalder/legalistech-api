import hashlib
import os
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from controllers.util.email_utils import notify_admin_new_contact  # asegúrate de que existe

class MailchimpController:
    def __init__(self):
        self.api_key = os.getenv("MAILCHIMP_MARKETING_KEY")
        self.server_prefix = os.getenv("MAILCHIMP_SERVER_PREFIX")
        self.list_id = os.getenv("MAILCHIMP_LIST_ID")  # Audiencia default
        self.client = MailchimpMarketing.Client()
        self.client.set_config({
            "api_key": self.api_key,
            "server": self.server_prefix
        })
    
    def list_audiences(self):
        try:
            response = self.client.lists.get_all_lists()
            print("Audiences found:")
            for lst in response.get("lists", []):
                print(f"- {lst['name']} — ID: {lst['id']}")
            return True, response
        except ApiClientError as error:
            print("Error listing audiences:", error.text)
            return False, error.text


    def add_contact(self, email, first_name, last_name, phone=None, note=None):
        member_info = {
            "email_address": email,
            "status": "subscribed",
            "merge_fields": {
                "FNAME": first_name,
                "LNAME": last_name
            }
        }

        if phone:
            member_info["merge_fields"]["PHONE"] = phone
        if note:
            member_info["notes"] = note

        try:
            # Agrega el contacto a la audiencia de Mailchimp
            response = self.client.lists.add_list_member(self.list_id, member_info)
            print("Contacto registrado en Mailchimp:", response)

            # Notifica al administrador por correo
            notify_admin_new_contact(
                name=first_name,
                last_name=last_name,
                email=email,
                phone=phone or "No proporcionado",
                message_text=note or "Sin mensaje"
            )

            return True, response

        except ApiClientError as error:
            print("Error registrando contacto:", error.text)
            return False, error.text
