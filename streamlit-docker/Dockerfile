FROM python:3.10
RUN apt-get update && apt-get install -y tor privoxy
EXPOSE 8501
WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN  pip3 install --upgrade pip && pip3 install -r requirements.txt
COPY . .

# Command overriden by docker-compose
CMD streamlit run Welcome.py