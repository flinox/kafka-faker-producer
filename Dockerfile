FROM openjdk:11.0.9.1-jre

ENV username="mocker"
# ENV TZ=America/Sao_Paulo
ENV TZ=UTC

RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y telnet netcat git jq nano

RUN groupadd -r ${username} --gid 1000
RUN useradd -ms /bin/bash -r -g ${username} ${username} --uid 1000

# Python
RUN apt-get install -y python3 python3-pip
RUN pip3 install --upgrade pip
RUN echo "alias python=python3" >> /home/${username}/.bashrc 
RUN echo "alias pip=pip3" >> /home/${username}/.bashrc 
COPY ./producer/requirements.txt /
RUN pip3 install -r /requirements.txt

# Configurar ambiente
RUN echo ". /app/scripts/environment_set.sh"  >> /home/${username}/.bashrc

WORKDIR /app/producer

USER ${username}