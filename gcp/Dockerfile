FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl nginx-light \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /usr/share/nginx/html/index.html /usr/share/nginx/html/50*.html

WORKDIR /app

COPY gcp/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY gcp/app.py /app/

COPY signup.html /usr/share/nginx/html/
COPY index.html /usr/share/nginx/html/
COPY *.html /usr/share/nginx/html/

COPY gcp/nginx-static.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn app:app --host 0.0.0.0 --port 8080"]