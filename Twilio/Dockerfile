FROM python:3.9
RUN apt-get update && apt-get install -y \
    libasound-dev \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    minimodem \
    python3-pip
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

WORKDIR ./app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--reload"]

