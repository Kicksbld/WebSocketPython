from websocket_server import WebsocketServer

from Context import Context
from Message import Message, MessageType

class WSServer:
    def __init__(self, ctx):
        self.host = ctx.host
        self.port = ctx.port
        self.server = WebsocketServer(host=self.host, port=self.port, loglevel=1)
        self.server.set_fn_new_client(self.on_new_client)
        self.server.set_fn_client_left(self.on_client_left)
        self.server.set_fn_message_received(self.on_message_received)


        self.clients = {}

    def on_new_client(self, client, server):
        print(f"[+] Client connecté: id={client['id']} addr={client['address']}")
        server.send_message(client, "Bienvenue !")

    def on_client_left(self, client, server):
        print(f"[-] Client déconnecté: id={client['id']}")

    def on_message_received(self, client, server, message):
        print(f"[{client['id']}] {message}")
        received_msg = Message.from_json(message)
        if received_msg.type == MessageType.DECLARATION:
            server.send_message(client, f"Declaration recue de {received_msg.emitter}")
            self.clients[received_msg.emitter] = client
        elif received_msg.type == MessageType.ENVOIE:
            receiver_client = self.clients.get(received_msg.receiver, None)
            if receiver_client:
                server.send_message(receiver_client, f"Message de {received_msg.emitter}: {received_msg.content}")
            else:
                server.send_message(client, f"Erreur: destinataire {received_msg.receiver} non trouvé")

    def start(self):
        print(f"Serveur WS sur ws://{self.host}:{self.port}")
        self.server.run_forever()

    @staticmethod
    def dev():
        return WSServer(Context.dev())

    @staticmethod
    def prod():
        return WSServer(Context.prod())

if __name__ == "__main__":
    s = WSServer.dev()
    s.start()

