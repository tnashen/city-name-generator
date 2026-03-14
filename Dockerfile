FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.1.1
COPY cities_data.py random_city.py llm_city.py job_queue.py app.py ./
COPY cities/ ./cities/
COPY templates/ ./templates/
COPY static/ ./static/
EXPOSE 5558
CMD ["python3", "app.py"]
