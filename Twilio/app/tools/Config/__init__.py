from pathlib import Path
import json

config_file = Path("secret.json")

if not config_file.exists():
    print("[+] Initializing secret config")
    sid = input("[+] TWILIO_ACCOUNT_SID: ")
    auth_token = input("[+] TWILIO_AUTH_TOKEN: ")
    with config_file.open("w") as f:
        f.write(json.dumps({
            "TWILIO_ACCOUNT_SID" : sid,
            "TWILIO_AUTH_TOKEN" : auth_token
        }))

else:
    with config_file.open() as f:
        data = json.loads(f.read())
    sid = data['TWILIO_ACCOUNT_SID']
    auth_token = data['TWILIO_AUTH_TOKEN']

config = {
    "twilio_sid" : sid,
    "twilio_auth" : auth_token
}