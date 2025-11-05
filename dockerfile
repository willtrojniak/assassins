FROM python:3.14-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Install Gunicorn
RUN pip install gunicorn

# Expose the port Gunicorn will listen on
EXPOSE 8000

# Command to run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
