FROM python:3.11-alpine
WORKDIR /bot
COPY . .
RUN pip install -r requirements.txt
CMD [ "python", "./main.py" ]
