FROM python:3.9-alpine
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
RUN apk update && apk add musl-dev gcc mariadb-dev libffi-dev g++ subversion automake make jpeg-dev
RUN pip install -r requirements.txt
COPY . /app
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "-p 80"]
