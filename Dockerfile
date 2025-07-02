WORKDIR /opt/program

# system packages
RUN apt-get update && apt-get install -y gcc libgomp1 && rm -rf /var/lib/apt/lists/*

# Python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy codes & model
COPY serve.py .
COPY wrapper.py .

# fix port
EXPOSE 8080

#set environment
ENV MODEL_PATH=/opt/ml/model

# run
ENTRYPOINT ["python", "serve.py"]
