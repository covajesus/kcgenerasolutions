import requests
import os
import hashlib
from dotenv import load_dotenv
from app.backend.classes.setting_class import SettingClass
from app.backend.db.models import CustomerModel
load_dotenv() 

class WhatsappClass:
    def __init__(self, db):
        self.db = db

    def send_dte(self, customer_phone, dte_type, folio, date, amount, dynamic_value): 
        url = "https://graph.facebook.com/v22.0/790586727468909/messages"
        token = os.getenv('META_TOKEN')

        # Formatear el número de teléfono
        phone_str = str(customer_phone).strip()
        if not phone_str.startswith("56"):
            customer_phone_formatted = "56" + phone_str
        else:
            customer_phone_formatted = phone_str

        payload = {
            "messaging_product": "whatsapp",
            "to": customer_phone_formatted,
            "type": "template",
            "template": {
                "name": "envio_dte_cliente_generado_v5",  # nombre EXACTO de tu plantilla
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": dte_type}, 
                            {"type": "text", "text": str(folio)},       # N° Boleta/Factura
                            {"type": "text", "text": date},             # Fecha
                            {"type": "text", "text": str(amount)},      # Monto
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": [
                            {
                                "type": "text",
                                "text": str(dynamic_value)  # valor dinámico para {{1}}
                            }
                        ]
                    }
                ]
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        print(f"[WHATSAPP] Status: {response.status_code}")
        print(f"[WHATSAPP] Response: {response.json()}")
        
        return response

    def send_new_order_alert(self, customer_name): 
        url = "https://graph.facebook.com/v22.0/790586727468909/messages"
        token = os.getenv('META_TOKEN')        
        setting_data = SettingClass(self.db).get(1)
        admin_phone = setting_data["setting_data"]["phone"]

        # Formatear el número de teléfono
        phone_str = str(admin_phone).strip()
        if not phone_str.startswith("56"):
            admin_phone_formatted = "56" + phone_str
        else:
            admin_phone_formatted = phone_str

        payload = {
            "messaging_product": "whatsapp",
            "to": admin_phone_formatted,
            "type": "template",
            "template": {
                "name": "alerta_nueva_orden",
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": customer_name}
                        ]
                    }
                ]
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        print(f"[WHATSAPP ALERT] Status: {response.status_code}")
        print(f"[WHATSAPP ALERT] Response: {response.json()}")
        
        return response

    def send_order_delivered_alert(self, customer_phone, id): 
        url = "https://graph.facebook.com/v22.0/790586727468909/messages"
        token = os.getenv('META_TOKEN')        

        # Formatear el número de teléfono
        phone_str = str(customer_phone).strip()
        if not phone_str.startswith("56"):
            customer_phone_formatted = "56" + phone_str
        else:
            customer_phone_formatted = phone_str

        payload = {
            "messaging_product": "whatsapp",
            "to": customer_phone_formatted,
            "type": "template",
            "template": {
                "name": "alerta_pedido_enviado",
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": id}
                        ]
                    }
                ]
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        print(f"[WHATSAPP ALERT] Status: {response.status_code}")
        print(f"[WHATSAPP ALERT] Response: {response.json()}")
        
        return response

    def send_rejected_payment_alert(self, customer_phone, id): 
        url = "https://graph.facebook.com/v22.0/790586727468909/messages"
        token = os.getenv('META_TOKEN')        

        # Formatear el número de teléfono
        phone_str = str(customer_phone).strip()
        if not phone_str.startswith("56"):
            customer_phone_formatted = "56" + phone_str
        else:
            customer_phone_formatted = phone_str

        payload = {
            "messaging_product": "whatsapp",
            "to": customer_phone_formatted,
            "type": "template",
            "template": {
                "name": "alerta_pago_rechazado",
                "language": {"code": "es"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": id}
                        ]
                    }
                ]
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        print(f"[WHATSAPP ALERT] Status: {response.status_code}")
        print(f"[WHATSAPP ALERT] Response: {response.json()}")
        
        return response

    

    def handle_message(self, message):
        print("📩 MENSAJE:", message)

        # Presupuestos / budgets fueron eliminados del backend.
        # Dejar handler como no-op para evitar errores.
        return {"status": "ignored"}

    def handle_status(self, status: dict):
        """
        Maneja estados enviados por WhatsApp:
        sent, delivered, read, failed
        """
        print("📬 STATUS WHATSAPP RECIBIDO")
        print(status)

        status_type = status.get("status")
        message_id = status.get("id")
        recipient = status.get("recipient_id")

        print(f"➡ Estado: {status_type}")
        print(f"➡ Message ID: {message_id}")
        print(f"➡ Destinatario: {recipient}")

        # Aquí puedes guardar en BD si quieres
        # ejemplo:
        # if status_type == "read":
        #     marcar_mensaje_leido(message_id)

    def send_autoreply(self, phone: str, text: str):
        url = "https://graph.facebook.com/v22.0/790586727468909/messages"
        token = os.getenv("META_TOKEN")

        if not phone.startswith("56"):
            phone = "56" + phone

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": text
            }
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)

        print("📨 AUTORESPONDER:", response.status_code, response.json())

