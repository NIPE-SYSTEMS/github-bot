FROM python:3

WORKDIR /app

COPY bot.py /app
COPY requirements.txt /app

RUN pip install -r requirements.txt

EXPOSE 8080
CMD [ "python", "bot.py", "config.yml" ]
