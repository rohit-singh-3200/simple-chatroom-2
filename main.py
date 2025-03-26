from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app=FastAPI()

html="""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Websockets</title>
    <!-- bootstrap -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.4.1/dist/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
</head>
<body>
    <div class="container mt-3">
        <h1>FastAPI WebSocket Chat</h1>
        <label for="username">Enter your name:</label>
        <input type="text" id="username" required />
        <button onclick="startChat()" class="btn btn-primary">Join Chat</button>

        <h2 id="user-heading" style="display:none;"> Your Name: <span id="ws-id"></span></h2>
        
        <form id="chat-form" style="display:none;" onsubmit="sendMessage(event)">
            <input type="text" class="formControl" id="messagetext" autocomplete="off"/>
            <button class="btn btn-outline-primary mt-1">Send</button>
        </form>
        <ul id='messages' class="mt-5"></ul>
    </div>

    <script>
        let ws;
        function startChat() {
            let username = document.getElementById("username").value.trim();
            if (!username) {
                alert("Please enter your name!");
                return;
            }
            document.querySelector("#ws-id").textContent = username;
            document.getElementById("user-heading").style.display = "block";
            document.getElementById("chat-form").style.display = "block";

            ws = new WebSocket(`ws://localhost:8000/ws/${username}`);
            
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                var content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };
        }

        function sendMessage(event) {
            var input = document.getElementById('messagetext');
            ws.send(input.value);
            input.value = '';
            event.preventDefault();
        }
    </script>
</body>

</html>"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can set specific origins instead of "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# two way connection
class connection_manager:
    def __init__(self):
        self.active_connections:list[WebSocket]=[]
    async def connect(self, websocket:WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self,websocket:WebSocket):
        self.active_connections.remove(websocket)
    async def send_personal_message(self,message:str,websocket:WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message:str):
        for connection in self.active_connections:
            await connection.send_text(message)
manager=connection_manager()

# apprun
@app.get("/")
async def get():
    return HTMLResponse(html)

# websocket
@app.websocket("/ws/{client_name}")
async def websocket_endpoint(websocket: WebSocket, client_name: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"{client_name}: {data}")
    except:
        manager.disconnect(websocket)
        await manager.broadcast(f"{client_name} has left the chat")




uvicorn.run(app)