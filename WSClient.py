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
        print(f"\n[server] {message}")

    def on_error(self, ws, error):
        print(f"[error] {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"[close] code={close_status_code} msg={close_msg}")

    def on_open(self, ws):
        print("[open] Connecté")
        message = Message(MessageType.DECLARATION, self.client_name, content="", receiver="")
        ws.send(message.to_json())

    def close(self):
        self.ws.close()

    def connect(self):
        self.ws.run_forever()

    def send(self, content, dest):
        message = Message(MessageType.ENVOIE, emitter="WSClient", content=content, receiver=dest)
        self.ws.send(message.to_json())
   

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "Client1"
    client = WSClient(Context.dev(), name)

    # Run WebSocket in background thread
    ws_thread = threading.Thread(target=client.connect, daemon=True)
    ws_thread.start()

    print(f"Client '{name}' started. Type 'receiver:message' to send (e.g., Client2:Hello!)")
    print("Type 'quit' to exit.\n")

    try:
        while True:
            user_input = input()
            if user_input.lower() == 'quit':
                break
            if ':' in user_input:
                receiver, content = user_input.split(':', 1)
                client.send(content.strip(), receiver.strip())
            else:
                print("Format: receiver:message")
    except KeyboardInterrupt:
        pass

    client.close()
