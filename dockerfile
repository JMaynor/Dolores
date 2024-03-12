FROM python:3.12
RUN apt-get -y update && apt-get install -y ffmpeg
RUN python -m pip install --upgrade pip
RUN mkdir /home/dolores
COPY dolores.py /home/dolores/dolores.py
COPY configload.py /home/dolores/configload.py
COPY config /home/dolores/config
COPY requirements.txt /home/dolores/requirements.txt
COPY modules /home/dolores/modules
RUN python -m venv /home/dolores/.venv
RUN . /home/dolores/.venv/bin/activate
RUN pip install -r /home/dolores/requirements.txt
CMD python /home/dolores/dolores.py
