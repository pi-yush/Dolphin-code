from fastapi import FastAPI, WebSocket, Header, Depends, Response, Form, Path
from fastapi.responses import FileResponse
import pyaudio
from typing import Optional

from twilio.twiml.voice_response import VoiceResponse, Start, Stream, Pause, Play
from twilio.rest import Client

from base64 import b64decode
import audioop
from functools import lru_cache

from tools.Config import config

app = FastAPI(description="Twilio client v2.0")
paudio = pyaudio.PyAudio()


sid = ""
url = ""

async def get_hosturl(host: Optional[str] = Header(...)):
    return host

@app.get("/voice")
@app.post("/voice")
async def twiml(host : Optional[str] = Depends(get_hosturl), CallSid: str = Form(...)):
    global sid, url
    print(f"[+] CallSid : {CallSid}")
    sid = CallSid
    url = host
    resp = VoiceResponse()
    start = Start()
    start.stream(
        url= "wss://" + host + "/ws"
    )
    pause = Pause(length=120)
    resp.append(start)
    resp.append(pause)
    return Response(str(resp) , media_type = "application/xml")

@app.get("/audio/{filepath}")
async def serve_wav(filepath):
    print(f"[+] Serving path {filepath}")
    return FileResponse(filepath)

@lru_cache
def get_twilio_client():
    account_sid = config["twilio_sid"]
    auth_token = config["twilio_auth"]

    client = Client(account_sid , auth_token)
    return client

@app.post("/send/{filepath}")
async def send_file(filepath):
    global sid , url
    print(f"[+] Sending {filepath}")

    client = get_twilio_client()
    resp = VoiceResponse()
    resp.play(url = f"https://{url}/audio/{filepath}")
    pause = Pause(length=120)
    resp.append(pause)
    call = client.calls(sid).update(twiml = str(resp))

    return {"done"}

@app.get("/status")
async def get_status():
    global sid
    client = get_twilio_client()
    call = client.calls(sid).fetch()
    return {"status" : call.status == "in-progress"}

@app.websocket("/ws")
async def stream(socket : WebSocket):
    print("[+] Starting socket")
    await socket.accept()
    data = await socket.receive_json()
    print("[+] Connected")

    data = await socket.receive_json()
    metadata = data['start']
    print(f"[+] StreamSid : {metadata['streamSid']}")

    stream = paudio.open(
        format = pyaudio.get_format_from_width(2),
        channels   = 1,
        rate = 8000,
        output = True,
    )
    buffer = b''
    thresh = 120
    while True:
        data = await socket.receive_json()
        print(f"[+] event : {data['event']}" , end="\r")
        if data['event'] == 'media':
            media = data['media']
            payload = media['payload']

            ulaw_data = b64decode(payload)
            ulaw_data = audioop.ulaw2lin(ulaw_data , 2)
            buffer += ulaw_data
            if len(buffer) < thresh:
                continue

            stream.write(buffer)
            buffer = b''
        if data['event'] == 'stop':
            stream.close()
            break
    await socket.close()

