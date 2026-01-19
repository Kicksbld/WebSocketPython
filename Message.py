class MessageType:
    DECLARATION = "declaration"
    ENVOIE = "envoie"
    RECPETION = "reception"

class Message:
    def __init__(self, type=None, emitter=None, content=None, receiver=None):
        self.type = type
        self.emitter = emitter
        self.content = content
        self.receiver = receiver
    
    @staticmethod
    def default_message():
        return Message("TOTO" "System", "This is a default message", "All")

    @staticmethod
    def from_json(json_data):
        import json
        data = json.loads(json_data)
        type = data['message_type']
        emitter = data['data']['emitter']
        content = data['data'].get('value', None)
        receiver = data['data'].get('receiver', None)
        return Message(type, emitter, content, receiver)

    def to_json(self):
        import json
        data = {
            "message_type": self.type,
            "data": {
                "emitter": self.emitter,
                "receiver": self.receiver,
                "value": self.content
            }
        }
        return json.dumps(data)


message = Message(MessageType.DECLARATION, emitter="System", content="This is a default message", receiver="All")
messageRebuild = Message.from_json(message.to_json())
assert message.to_json() == messageRebuild.to_json()