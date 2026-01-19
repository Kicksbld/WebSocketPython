import websocket
import threading
import sys
from Context import Context
from Message import Message, MessageType

class WSClient:

    def __init__(self, ctx, client_name):
        self.client_name = client_name
        self.ws = websocket.WebSocketApp(
            ctx.url(),
            on_open = self.on_open,
            on_message = self.on_message,
            on_error = self.on_error,
            on_close = self.on_close,
        )

    def on_message(self, ws, message):
        try:
            msg = Message.from_json(message)
            self.handle_received_message(msg)
        except Exception:
            print(f"\n[server] {message}")

    def handle_received_message(self, msg):
        """Gere les messages recus selon leur type."""
        if msg.type == MessageType.RECEPTION:
            print(f"\n[{msg.emitter}] {msg.content}")
            self.send_ack(msg.emitter)
        elif msg.type == MessageType.SYS_MESSAGE:
            self.handle_sys_message(msg)
        elif msg.type == MessageType.WARNING:
            print(f"\n[WARNING] {msg.content}")
        else:
            print(f"\n[{msg.type}] {msg.content}")

    def handle_sys_message(self, msg):
        """Gere les messages systeme (ping, confirmations)."""
        if msg.content == "**ping**":
            pong = Message.pong(self.client_name)
            self.ws.send(pong.to_json())
            print("\n[PING] Recu, pong envoye")
        elif msg.content == "OK":
            print("\n[OK] Message envoye avec succes")
        elif msg.content == "message recu":
            print("\n[ACK] Destinataire a recu le message")
        elif msg.content == "message non recu":
            print("\n[ACK] Destinataire n'a pas confirme la reception")
        elif msg.content == "Declaration recue":
            print("\n[SERVER] Declaration confirmee")

    def send_ack(self, original_emitter):
        """Envoie un accuse de reception MESSAGE OK."""
        ack = Message.sys_message(self.client_name, "MESSAGE OK", original_emitter)
        self.ws.send(ack.to_json())

    def on_error(self, ws, error):
        print(f"[error] {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"[close] code={close_status_code} msg={close_msg}")

    def on_open(self, ws):
        print("[open] Connecte")
        message = Message(MessageType.DECLARATION, self.client_name, content="", receiver="")
        ws.send(message.to_json())

    def close(self):
        self.ws.close()

    def connect(self):
        self.ws.run_forever()

    def send(self, content, dest):
        message = Message(MessageType.ENVOIE, emitter=self.client_name, content=content, receiver=dest)
        self.ws.send(message.to_json())

    def disconnect(self):
        """Envoie un message de deconnexion propre."""
        disconnect_msg = Message.disconnect(self.client_name)
        self.ws.send(disconnect_msg.to_json())
   

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "Client1"
    client = WSClient(Context.dev(), name)

    # Run WebSocket in background thread
    ws_thread = threading.Thread(target=client.connect, daemon=True)
    ws_thread.start()

    print(f"Client '{name}' started. Type 'receiver:message' to send (e.g., Bob:Hello!)")
    print("Type 'quit' to exit.\n")

    try:
        while True:
            user_input = input()
            if user_input.lower() == 'quit':
                client.disconnect()
                break
            if ':' in user_input:
                receiver, content = user_input.split(':', 1)
                client.send(content.strip(), receiver.strip())
            else:
                print("Format: receiver:message")
    except KeyboardInterrupt:
        try:
            client.disconnect()
        except Exception:
            pass

    client.close()
