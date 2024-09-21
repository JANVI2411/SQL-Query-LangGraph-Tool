# Start with a RHEL Universal Base Image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy all files into the container
COPY . /app

# Make the startup script executable
RUN chmod +x /app/start.sh

# Update and install Python, pip, and other dependencies
# RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt && \
    apt-get clean all && rm -rf /var/cache/yum /var/cache/dnf /root/.cache/pip

# Expose the required ports for FastAPI and Streamlit
EXPOSE 9000

# Start both FastAPI and Streamlit using the startup script
CMD ["sh","/app/start.sh"]