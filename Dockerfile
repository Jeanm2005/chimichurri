# Python image to use.
FROM python:3.10

# Expose 8080 as the port
EXPOSE 8080

# Set the working directory to /app
WORKDIR /app

# Copy the directory contents into the container
COPY . ./

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Add the root directory to Python path so imports work
ENV PYTHONPATH="/app:${PYTHONPATH}"

# The main command to run when the container starts.
ENTRYPOINT ["streamlit", "run", "frontend/app.py"]
