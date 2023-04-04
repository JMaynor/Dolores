FROM python
RUN apt-get -y update && apt-get install -y ffmpeg
RUN python -m pip install --upgrade pip
RUN pip install py-cord[voice]
# RUN pip install sqlalchemy
# RUN pip install chatterbot==1.0.4
RUN pip install pyyaml
# RUN pip install chatterbot-corpus==1.2.0
RUN pip install yt-dlp
RUN pip install pytz
RUN pip install requests
RUN pip install pandas
RUN pip install nltk
RUN pip install pint
RUN pip install mathparse
RUN pip install ftfy
# RUN pip list
# RUN mkdir C:\home\dolores
RUN mkdir /home/dolores
COPY dolores.py /home/dolores/dolores.py
COPY config /home/dolores/config
COPY sqlalchemy /home/dolores/sqlalchemy
COPY chatterbot /home/dolores/chatterbot
COPY chatterbot_corpus /home/dolores/chatterbot_corpus
CMD python /home/dolores/dolores.py
