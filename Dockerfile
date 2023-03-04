FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python3" , "main.py", '0.0.0.0', '8081', '146.185.242.0', '8090', 'admins']