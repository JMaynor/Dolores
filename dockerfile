FROM python
RUN apt-get -y update && apt-get install -y ffmpeg
RUN python -m pip install --upgrade pip
RUN pip install discord.py[voice]
RUN pip install chatterbot==1.0.4
RUN pip install chatterbot-corpus==1.2.0
RUN pip install youtube-dl
RUN pip install pytz
RUN pip install requests
RUN pip install pandas
RUN pip list
# RUN mkdir C:\home\dolores
RUN mkdir /home/dolores
COPY dolores.py /home/dolores/dolores.py
COPY database /home/dolores/database
COPY config.yml /home/dolores/config.yml
CMD python /home/dolores/dolores.py
