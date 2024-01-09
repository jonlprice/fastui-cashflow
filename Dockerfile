#
FROM python:3.11

#
WORKDIR /code

#
COPY ./requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

#
COPY ./app /code/app
COPY ./static /code/static
COPY ./templates /code/templates

#
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
