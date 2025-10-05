import os
import psycopg2
from psycopg2.extras import Json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Extra

# --- Modelo de Dados Dinâmico (Pydantic) ---
# Usar `Extra.allow` permite que o modelo aceite quaisquer campos
# que venham do SurveyJS (question1, question2, etc.) sem listá-los explicitamente.
# Isso torna o backend muito mais flexível a mudanças no formulário.
class SurveyData(BaseModel, extra=Extra.allow):
    pass

# --- Criação da Aplicação FastAPI ---
app = FastAPI(
    title="SurveyNexa API",
    description="API para receber e salvar dados do SurveyJS da Nexa.",
    version="1.0.0"
)

# --- Configuração do Banco de Dados a partir de Variáveis de Ambiente ---
# Esta é a forma segura e correta para deploy.
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
    # Validação para garantir que as variáveis de ambiente foram carregadas
    if not all([DB_NAME, DB_USER, DB_PASS, DB_HOST]):
        raise HTTPException(status_code=500, detail="As variáveis de ambiente do banco de dados não estão configuradas no servidor.")

    conn = None
    try:
        # Conecta ao banco de dados PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Comando SQL para inserir os dados JSONB na tabela
        sql_command = """
            INSERT INTO respostas_survey (dados_respostas)
            VALUES (%s) RETURNING id;
        """

        # Converte o modelo Pydantic para um dicionário e depois para o formato Json
        survey_data_dict = data.dict()
        cursor.execute(sql_command, (Json(survey_data_dict),))
        
        # Recupera o ID da inserção para confirmação
        new_id = cursor.fetchone()[0]

        # Confirma a transação
        conn.commit()

        return {"message": "Dados salvos com sucesso!", "id_resposta": new_id}

    except psycopg2.Error as e:
        # Em caso de erro de banco de dados, imprime o erro no log do servidor
        print(f"Erro de banco de dados: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar os dados no banco de dados.")
    except Exception as e:
        # Para qualquer outro tipo de erro
        print(f"Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro interno no servidor.")
    finally:
        # Garante que a conexão com o banco seja sempre fechada
        if conn:
            cursor.close()
            conn.close()

# --- Endpoint raiz para teste de saúde da API ---
@app.get("/")
def read_root():
    return {"status": "SurveyNexa API está no ar!"}