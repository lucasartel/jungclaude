FROM python:3.11-slim

# Variáveis para otimização
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instalar apenas o essencial do sistema (se precisar de gcc para alguma lib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python SEM cache
RUN pip install --no-cache-dir -r requirements.txt

# Copiar apenas o código necessário
COPY *.py .
COPY .env .

# Criar diretório de dados (se usar SQLite)
RUN mkdir -p /data

# Porta padrão
EXPOSE 8000

# Iniciar bot
CMD ["python", "telegram_bot.py"]