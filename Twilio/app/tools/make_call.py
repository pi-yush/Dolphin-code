from twilio.rest import Client
from Config import config


def make_call():
    client = Client(
        config["twilio_sid"],
        config["twilio_auth"]
    )

    return client.calls.create(
        url = '[url to hosted twilio script]',
        to  = '[number to call to]',
        from_ =  '[twilio number]'
    )

if __name__ == "__main__":
    make_call()
