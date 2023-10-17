FROM python:3.10
WORKDIR /code

RUN apt update && sudo apt -y install libsndfile1
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

