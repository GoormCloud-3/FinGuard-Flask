FROM python:3.9-slim

WORKDIR /opt/program

# runtime-libs for xgboost
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

# required python packages 
#(XGBoost Model Ver: 1.5.x)
RUN pip install --no-cache-dir flask==2.3.3 xgboost==1.5.0 pandas numpy 

# copy infernce script
COPY serve.py .

# set the script for serving
ENV PYTHONUNBUFFERED=1

# base THRESHOLD
# THRESHOLD=0.5

#port 
EXPOSE 8080

# entry point
ENTRYPOINT ["python","serve.py"]
