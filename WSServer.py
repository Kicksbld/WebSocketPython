from websocket_server import WebsocketServer
import threading
import time

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
        self.pong_received = {}
        self.ping_interval = 30
        self.ping_timeout = 10

    def search_receiver(self, receiver_name):
        """Recherche un client par son nom."""
        return self.clients.get(receiver_name, None)

    def send_json(self, client, message):
        """Envoie un message au format JSON."""
        self.server.send_message(client, message.to_json())

    def on_new_client(self, client, server):
        print(f"[+] Client connecte: id={client['id']} addr={client['address']}")
        welcome_msg = Message.reception("SERVER", "Bienvenue !", "")
        self.send_json(client, welcome_msg)

    def on_client_left(self, client, server):
        client_name = None
        for name, c in list(self.clients.items()):
            if c['id'] == client['id']:
                client_name = name
                break
        if client_name:
            del self.clients[client_name]
            if client_name in self.pong_received:
                del self.pong_received[client_name]
        print(f"[-] Client deconnecte: id={client['id']} name={client_name}")

    def on_message_received(self, client, server, message):
        print(f"[{client['id']}] {message}")
        received_msg = Message.from_json(message)

        if received_msg.type == MessageType.DECLARATION:
            self.handle_declaration(client, received_msg)
        elif received_msg.type == MessageType.ENVOIE:
            self.handle_envoie(client, received_msg)
        elif received_msg.type == MessageType.SYS_MESSAGE:
            self.handle_sys_message(client, received_msg)

    def handle_declaration(self, client, msg):
        """Gere l'enregistrement d'un nouveau client."""
        self.clients[msg.emitter] = client
        response = Message.reception("SERVER", "Declaration recue", msg.emitter)
        self.send_json(client, response)
        print(f"[DECLARATION] {msg.emitter} enregistre")

    def handle_envoie(self, client, msg):
        """Gere l'envoi d'un message vers un destinataire."""
        receiver_client = self.search_receiver(msg.receiver)

        if receiver_client is None:
            warning = Message.warning("SERVER", "E40: Receiver not found", msg.emitter)
            self.send_json(client, warning)
            print(f"[WARNING] Receiver {msg.receiver} not found")
        else:
            reception = Message.reception(msg.emitter, msg.content, msg.receiver)
            self.send_json(receiver_client, reception)
            ok_msg = Message.sys_message("SERVER", "OK", msg.emitter)
            self.send_json(client, ok_msg)
            print(f"[ENVOIE] {msg.emitter} -> {msg.receiver}: {msg.content}")

    def handle_sys_message(self, client, msg):
        """Gere les messages systeme (disconnect, pong, ack)."""
        if msg.content == "Disconnect":
            self.handle_disconnect(client, msg)
        elif msg.content == "**pong**":
            self.handle_pong(client, msg)
        elif msg.content == "MESSAGE OK":
            self.handle_message_ack(client, msg)

    def handle_disconnect(self, client, msg):
        """Gere la deconnexion gracieuse d'un client."""
        client_name = msg.emitter
        if client_name in self.clients:
            del self.clients[client_name]
            if client_name in self.pong_received:
                del self.pong_received[client_name]
            print(f"[DISCONNECT] {client_name} s'est deconnecte")

    def handle_pong(self, client, msg):
        """Enregistre la reception d'un pong."""
        client_name = msg.emitter
        self.pong_received[client_name] = True
        print(f"[PONG] Recu de {client_name}")

    def handle_message_ack(self, client, msg):
        """Gere la reception d'un accuse MESSAGE OK."""
        sender_name = msg.receiver
        sender_client = self.search_receiver(sender_name)
        if sender_client:
            ack_confirm = Message.sys_message("SERVER", "message recu", sender_name)
            self.send_json(sender_client, ack_confirm)
            print(f"[ACK] {msg.emitter} a confirme reception a {sender_name}")

    def start_ping_thread(self):
        """Demarre un thread qui envoie des pings periodiques."""
        def ping_loop():
            while True:
                time.sleep(self.ping_interval)
                self.send_pings()
        ping_thread = threading.Thread(target=ping_loop, daemon=True)
        ping_thread.start()

    def send_pings(self):
        """Envoie un ping a tous les clients."""
        for name in list(self.clients.keys()):
            self.pong_received[name] = False

        ping_msg = Message.ping()
        for name, client in list(self.clients.items()):
            try:
                self.send_json(client, ping_msg)
                print(f"[PING] Envoye a {name}")
            except Exception as e:
                print(f"[PING ERROR] {name}: {e}")

        time.sleep(self.ping_timeout)
        self.check_pong_responses()

    def check_pong_responses(self):
        """Supprime les clients qui n'ont pas repondu au ping."""
        for name in list(self.clients.keys()):
            if not self.pong_received.get(name, False):
                print(f"[TIMEOUT] {name} n'a pas repondu au ping, suppression")
                del self.clients[name]
                if name in self.pong_received:
                    del self.pong_received[name]

    def start(self):
        print(f"Serveur WS sur ws://{self.host}:{self.port}")
        self.start_ping_thread()
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

