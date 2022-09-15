# Twilio Server implementaion for Dolphin

## Preqrequisite
- Create a [twilio](https://www.twilio.com/try-twilio) account or use a previous account.
- Get a phone number on twilio.
- Get a server with registered domain and TLS certificate
- If previous step is not possible, you can test the scripts with [ngrok](https://ngrok.com/)

## Depenedencies
- PortAudio is a requirement for building PyAudio.

- You can locally [build](http://www.portaudio.com/docs/v19-doxydocs/compile_linux.html) portaudio or for debian based distros use

        sudo apt install -y libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0 minimodem

- Install all other requirements using

        pip install -r requirements.txt

## Running
- Tested with ngrok: Set a webhook using the generated ngrok url on the twilio website.
- Get `account_sid` and `account_token` from the twilio console.
- Change to app folder and run `uvicorn main:app --host 0.0.0.0 --reload`. This will start the twilio server.

## Testing
For both these tests, it is assumed that the previous steps are working properly.
- For feasibility testing run `app/tools/dolphin_test.py`. In the file `app/tools/make_call.py` on line 11 make the required changes.
- For dolphin testing run `Main_Experiment/ack_optimized_server.py`
