FROM python:3.13-slim

WORKDIR /proj_root

# Copy requirements file and install app dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt 

EXPOSE 8443

# copy in project files
COPY . .

CMD ["python", "app/app.py"]
