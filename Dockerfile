FROM python:3.10

WORKDIR /

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY app /app

RUN mkdir /app/static
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
