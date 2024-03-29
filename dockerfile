FROM python:3.12
RUN apt-get -y update && apt-get install -y ffmpeg
RUN python -m pip install --upgrade pip
RUN mkdir /home/dolores
COPY . /home/dolores
RUN python -m venv /home/dolores/.venv
RUN . /home/dolores/.venv/bin/activate
RUN pip install -r /home/dolores/requirements.txt
CMD python /home/dolores/dolores.py
