FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install flask requests

# Copy the application code
COPY app.py .

# Expose the port
EXPOSE 7860

# Run the application
CMD ["python", "app.py"]