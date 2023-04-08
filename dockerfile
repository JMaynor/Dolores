FROM python
RUN apt-get -y update && apt-get install -y ffmpeg
RUN python -m pip install --upgrade pip
RUN mkdir /home/dolores
COPY dolores.py /home/dolores/dolores.py
COPY config /home/dolores/config
COPY sqlalchemy /home/dolores/sqlalchemy
COPY chatterbot /home/dolores/chatterbot
COPY chatterbot_corpus /home/dolores/chatterbot_corpus
COPY requirements.txt /home/dolores/requirements.txt
RUN python -m venv /home/dolores/.venv
RUN . /home/dolores/.venv/bin/activate
RUN pip install -r /home/dolores/requirements.txt
CMD python /home/dolores/dolores.py
