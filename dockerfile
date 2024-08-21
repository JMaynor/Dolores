FROM python:3.12
RUN python -m pip install --upgrade pip
RUN mkdir /home/dolores
COPY . /home/dolores
WORKDIR /home/dolores
RUN python -m venv /home/dolores/.venv
RUN . /home/dolores/.venv/bin/activate
RUN pip install -r /home/dolores/requirements.txt
CMD python /home/dolores/src/dolores.py
