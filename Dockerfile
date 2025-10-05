# Usa uma imagem oficial do Python, leve e segura.
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container.
WORKDIR /app

# Copia o arquivo de dependências primeiro para aproveitar o cache do Docker.
COPY requirements.txt .

# Instala as dependências.
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação para o diretório de trabalho.
COPY . .

# Expõe a porta que a aplicação vai usar dentro do container.
EXPOSE 80

# Comando para iniciar a aplicação quando o container for executado.
# O host 0.0.0.0 é fundamental para que o Easypanel consiga se conectar.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]