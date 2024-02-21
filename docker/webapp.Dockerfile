# webapp/webapp.derper.webapp.Dockerfile
FROM python:3.10-slim
LABEL authors="laqua_f"
WORKDIR /app

RUN apt-get update && apt-get install -y \
#    build-essential \
   curl \
#    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

#RUN --mount=type=ssh,id=myproject git clone sgit@github.com:laqua-stack/imagine-imaging.eu.git
#COPY ../../docker_requirements.txt /app/docker_requirements.txt

RUN --mount=type=secret,id=acc_token ACC_TOKEN=$(cat /run/secrets/acc_token) \
    && git clone https://$ACC_TOKEN@github.com/Baessler-Lab/dicom-base.git /dicom-base
COPY ../.. /app/

RUN pip install --no-cache-dir --upgrade -r /app/docker_requirements.txt
RUN pip install -e /dicom-base
#RUN pip install -e /llm-tag

ENV HOST=0.0.0.0
#ENV LISTEN_PORT 8510
#EXPOSE 8510
#ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PYTHONPATH "${PYTHONPATH}:/app:/app/swagtag"

HEALTHCHECK CMD curl --fail http://localhost:8510/web/_stcore/health

ENTRYPOINT ["streamlit", \
            "run", \
            "swagtag/main.py", \
            "--server.port=8510", \
            "--server.fileWatcherType=none", \
            "--server.enableCORS=false", \
            "--server.enableXsrfProtection=false", \
            "--server.enableWebsocketCompression=false",\
            "--server.baseUrlPath=/web"]