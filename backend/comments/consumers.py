from channels.generic.websocket import AsyncJsonWebsocketConsumer

GROUP_NAME = "comments"


class CommentsConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Single public group used by all clients
        self.group_name = GROUP_NAME
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive_json(self, content, **kwargs):
        # Lightweight echo for manual testing
        if "ping" in content:
            await self.send_json({"pong": content.get("ping")})
            return

    # "comment.event" -> "comment_event"
    async def comment_event(self, event):
        # Always send a flat payload to the client
        # event shape: {"type": "comment.event", "payload": {...flat...}}
        await self.send_json(event["payload"])
