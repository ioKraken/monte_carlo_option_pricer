FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py theme.py monte_carlo.py greeks.py market_data.py ./
COPY .streamlit .streamlit

# Most hosts (Render, Fly, Cloud Run) inject $PORT; default to Streamlit's 8501
ENV PORT=8501
EXPOSE 8501
HEALTHCHECK CMD python -c "import os,urllib.request;urllib.request.urlopen(f'http://localhost:{os.environ[\"PORT\"]}/_stcore/health')"
CMD ["sh", "-c", "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"]
