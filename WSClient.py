import websocket
import threading
import base64

from Context import Context
from Message import Message, MessageType


class WSClient:
    def __init__(self, ctx, username="Client"):
        self.username = username
        self.connected = False
        self.connected_clients = []
        self.ws = websocket.WebSocketApp(
            ctx.url(),
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

    def on_message(self, ws, message):
        received_msg = Message.from_json(message)

        # Répondre au ping du serveur
        if received_msg.message_type == MessageType.SYS_MESSAGE and received_msg.value == "ping":
            pong_msg = Message(MessageType.SYS_MESSAGE, emitter=self.username, receiver="", value="pong")
            ws.send(pong_msg.to_json())
            return

        # Gestion de la liste des clients
        if received_msg.message_type == MessageType.RECEPTION.CLIENT_LIST:
            self.connected_clients = [c for c in received_msg.value if c != self.username]
            print(f"\n[info] Clients connectés: {self.connected_clients}")
            return

        # Affichage selon le type de message
        print(f"\n[{received_msg.emitter}] {received_msg.value}")

        # Accusé de réception pour les messages RECEPTION
        if received_msg.message_type in [MessageType.RECEPTION.TEXT, MessageType.RECEPTION.IMAGE, MessageType.RECEPTION.AUDIO, MessageType.RECEPTION.VIDEO]:
            ack_msg = Message(MessageType.SYS_MESSAGE, emitter=self.username, receiver="", value="MESSAGE OK")
            ws.send(ack_msg.to_json())

    def on_error(self, ws, error):
        print(f"\n[error] {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"\n[close] code={close_status_code} msg={close_msg}")
        self.connected = False

    def on_open(self, ws):
        print("[open] connecté")
        self.connected = True
        message = Message(MessageType.DECLARATION, emitter=self.username, receiver="", value="")
        ws.send(message.to_json())

        input_thread = threading.Thread(target=self.input_loop, daemon=True)
        input_thread.start()

    def select_recipient(self):
        """Affiche un menu de sélection du destinataire"""
        print("\n--- Choisir le destinataire ---")
        print("0. Everyone (tous)")
        for i, client in enumerate(self.connected_clients, 1):
            print(f"{i}. {client}")
        print("--------------------------------")

        while True:
            try:
                choice = input("Numéro du destinataire (ou 'disconnect' pour quitter): ")
                if choice.lower() == "disconnect":
                    return None
                choice = int(choice)
                if choice == 0:
                    return "ALL"
                elif 1 <= choice <= len(self.connected_clients):
                    return self.connected_clients[choice - 1]
                else:
                    print("Choix invalide")
            except ValueError:
                print("Entrez un numéro valide")

    def input_loop(self):
        print(f"\nChat démarré en tant que '{self.username}'")
        print("Commandes spéciales: 'disconnect', 'img:dest:chemin', 'audio:dest:chemin', 'video:dest:chemin'\n")

        while self.connected:
            try:
                dest = self.select_recipient()

                if dest is None:
                    disconnect_msg = Message(MessageType.SYS_MESSAGE, emitter=self.username, receiver="", value="Disconnect")
                    self.ws.send(disconnect_msg.to_json())
                    self.ws.close()
                    break

                content = input("Message: ")

                if content.lower() == "disconnect":
                    disconnect_msg = Message(MessageType.SYS_MESSAGE, emitter=self.username, receiver="", value="Disconnect")
                    self.ws.send(disconnect_msg.to_json())
                    self.ws.close()
                    break
                elif content.lower().startswith("img:"):
                    filepath = content[4:].strip()
                    self.send_image(filepath, dest)
                    print(f"[image envoyée à {dest}]")
                elif content.lower().startswith("audio:"):
                    filepath = content[6:].strip()
                    self.send_audio(filepath, dest)
                    print(f"[audio envoyé à {dest}]")
                elif content.lower().startswith("video:"):
                    filepath = content[6:].strip()
                    self.send_video(filepath, dest)
                    print(f"[video envoyée à {dest}]")
                else:
                    self.send(content, dest)
                    print(f"[envoyé à {dest}] {content}")

            except EOFError:
                break

    def connect(self):
        self.ws.run_forever()

    def send(self, value, dest):
        message = Message(MessageType.ENVOI.TEXT, emitter=self.username, receiver=dest, value=value)
        self.ws.send(message.to_json())

    def send_image(self, filepath, dest):
        with open(filepath, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
        value = f"IMG:{img_base64}"
        message = Message(MessageType.ENVOI.IMAGE, emitter=self.username, receiver=dest, value=value)
        self.ws.send(message.to_json())

    def send_audio(self, filepath, dest):
        with open(filepath, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")
        value = f"AUDIO:{audio_base64}"
        message = Message(MessageType.ENVOI.AUDIO, emitter=self.username, receiver=dest, value=value)
        self.ws.send(message.to_json())

    def send_video(self, filepath, dest):
        with open(filepath, "rb") as f:
            video_base64 = base64.b64encode(f.read()).decode("utf-8")
        value = f"VIDEO:{video_base64}"
        message = Message(MessageType.ENVOI.VIDEO, emitter=self.username, receiver=dest, value=value)
        self.ws.send(message.to_json())

    @staticmethod
    def dev(username="Client"):
        return WSClient(Context.dev(), username)

    @staticmethod
    def prod(username="Client"):
        return WSClient(Context.prod(), username)

if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "Client"
    client = WSClient.prod(username)
    client.connect()