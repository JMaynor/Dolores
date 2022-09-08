FROM python
RUN apt-get -y update && apt-get install -y ffmpeg
RUN python -m pip install --upgrade pip
RUN pip install discord.py[voice]
# RUN pip install sqlalchemy
# RUN pip install chatterbot==1.0.4
RUN pip install pyyaml
# RUN pip install chatterbot-corpus==1.2.0
RUN pip install yt-dlp
RUN pip install pytz
RUN pip install requests
RUN pip install pandas
RUN pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116
RUN pip install diffusers
RUN pip install transformers
RUN pip install ftfy
# RUN pip list
# RUN mkdir C:\home\dolores
RUN mkdir /home/dolores
COPY dolores.py /home/dolores/dolores.py
COPY config /home/dolores/config
CMD python /home/dolores/dolores.py
