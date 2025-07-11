from flask import Blueprint, request, jsonify
from controllers.mailchimpController import MailchimpController

contact_Router = Blueprint("contact", __name__)
mailchimp = MailchimpController()

@contact_Router.route("/contact", methods=["POST"])
def handle_contact():
    try:
        data = request.get_json()

        required_fields = ["email", "nombre", "apellidos"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo obligatorio faltante: {field}"}), 400

        email = data["email"]
        nombre = data["nombre"]
        apellidos = data["apellidos"]
        telefono = data.get("telefono")
        mensaje = data.get("mensaje")

        success, result = mailchimp.add_contact(
            email=email,
            first_name=nombre,
            last_name=apellidos,
            phone=telefono,
            note=mensaje
        )

        if success:
            return jsonify({"message": "Contacto registrado correctamente"}), 200
        else:
            return jsonify({"error": f"Error desde Mailchimp: {result}"}), 400

    except Exception as e:
        return jsonify({"error": f"Error interno al procesar el formulario: {str(e)}"}), 500

@contact_Router.route("/audiences", methods=["GET"])
def list_mailchimp_audiences():
    success, result = mailchimp.list_audiences()
    if success:
        return result, 200
    else:
        return {"error": result}, 400
