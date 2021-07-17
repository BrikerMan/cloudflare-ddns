FROM brikerman/ubuntu20_python3:3.8.9

ARG VERSION="0.0.1"

ENV PYTHONPATH=/code/ \
  PYTHONIOENCODING=utf-8 \
  API_RUN_ENV=docker \
  TERM=xterm-256color \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  API_VERSION=$VERSION

WORKDIR /app
EXPOSE 80

COPY . /app/
RUN pip3 install --no-cache-dir -r requirements.txt --use-feature=2020-resolver

CMD python main.py