import os
import psycopg2
from psycopg2.extras import Json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Extra
from fastapi.middleware.cors import CORSMiddleware # <<< 1. IMPORTE O MIDDLEWARE

# --- Modelo de Dados Dinâmico (Pydantic) ---
class SurveyData(BaseModel, extra=Extra.allow):
    pass

# --- Criação da Aplicação FastAPI ---
app = FastAPI(
    title="SurveyNexa API",
    description="API para receber e salvar dados do SurveyJS da Nexa.",
    version="1.0.0"
)

# --- 2. ADICIONE O BLOCO DE CONFIGURAÇÃO DO CORS ---
# Esta lista contém os domínios do front-end que podem fazer requisições à sua API.
origins = [
    "https://forms.cortix.info",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Permite as origens da lista
    allow_credentials=True,
    allow_methods=["*"],    # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],    # Permite todos os cabeçalhos
)

# --- Configuração do Banco de Dados a partir de Variáveis de Ambiente ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")

# --- Endpoint para receber os dados ---
@app.post("/post")
def save_survey_data(data: SurveyData):
    """
    Este endpoint recebe os dados do SurveyJS via POST, valida a estrutura
    e os salva na tabela 'respostas_survey' do PostgreSQL.
    """
    if not all([DB_NAME, DB_USER, DB_PASS, DB_HOST]):
        raise HTTPException(status_code=500, detail="As variáveis de ambiente do banco de dados não estão configuradas no servidor.")

    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        sql_command = "INSERT INTO respostas_survey (dados_respostas) VALUES (%s) RETURNING id;"
        survey_data_dict = data.dict()
        cursor.execute(sql_command, (Json(survey_data_dict),))
        new_id = cursor.fetchone()[0]
        conn.commit()
        return {"message": "Dados salvos com sucesso!", "id_resposta": new_id}
    except psycopg2.Error as e:
        print(f"Erro de banco de dados: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar os dados no banco de dados.")
    except Exception as e:
        print(f"Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno no servidor.")
    finally:
        if conn:
            cursor.close()
            conn.close()

# --- Endpoint raiz para teste de saúde da API ---
@app.get("/")
def read_root():
    return {"status": "SurveyNexa API está no ar!"}