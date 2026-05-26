import streamlit as st
from redcap import Project
import requests
from datetime import datetime

# Configuração da página do Streamlit
st.set_page_config(page_title="Check-in Pós-Graduação", page_icon="🎓", layout="centered")

# Configurações de conexão com o REDCap do HCFMB Unesp (Utilizando os Secrets seguros)
REDCAP_API_URL = st.secrets["REDCAP_API_URL"]
TOKEN = st.secrets["REDCAP_TOKEN"]

@st.cache_resource
def get_redcap_project():
    try:
        return Project(REDCAP_API_URL, TOKEN)
    except Exception as e:
        st.error(f"Erro ao conectar com a API do REDCap: {e}")
        return None

project = get_redcap_project()

# Lista de opções para as barras horizontais (Exatamente como o REDCap espera)
opcoes_progresso = [
    "0% → Não iniciei",
    "25% → Início",
    "50% → Em andamento",
    "75% → Quase finalizado",
    "100% → Concluído"
]

# Dicionário reverso para descobrir o código numérico ("0", "25", etc.) a partir do texto selecionado
mapa_valores_redcap = {
    "0% → Não iniciei": "0",
    "25% → Início": "25",
    "50% → Em andamento": "50",
    "75% → Quase finalizado": "75",
    "100% → Concluído": "100"
}

# Dicionários de mapeamento para as opções dos blocos seguintes (Radios)
opcoes_organizacao = {
    "Nada organizado": "0",
    "Pouco": "1",
    "Moderado": "2",
    "Bem-organizado": "3"
}

opcoes_suporte = {
    "Muito insatisfeito": "0",
    "Insatisfeito": "1",
    "Satisfeito": "2",
    "Muito satisfeito": "3"
}

opcoes_produtividade = {"Baixa": "1", "Moderada": "2", "Alta": "3"}
opcoes_atrasado = {"Não": "1", "Um pouco": "2", "Sim": "3"}

st.title("🎓 Check-in de Progresso da Pós-Graduação")
st.write("Por favor, preencha as informações abaixo para atualizar seu andamento.")

# Formulário único do Streamlit
with st.form("form_redcap", clear_on_submit=False):
    
    st.header("Identificação Geral")
    record_id = st.text_input("Record ID (Código do Aluno) *", help="Insira o identificador único do registro.")
    
    # Tratamento de Data/Horário
    data_envio_redcap = datetime.now().strftime("%Y-%m-%d")
    data_visualizacao = datetime.now().strftime("%d/%m/%Y")
    horario_atual = datetime.now().strftime("%H:%M")
    
    st.info(f"📅 **Data:** {data_visualizacao} | ⏰ **Horário:** {horario_atual}")

    # --- INSTRUMENTO 1: Check-in de Progresso ---
    st.markdown("---")
    st.subheader("BLOCO 1 - Andamento Acadêmico")
    
    # Nova abordagem de barra de rolagem horizontal usando select_slider
    andamento_academico = st.select_slider("Andamento Acadêmico *", options=opcoes_progresso)
    
    # Upload do arquivo de cronograma
    arquivo_cronograma = st.file_uploader("Envie aqui seu cronograma (PDF, DOCX, etc.) *", type=["pdf", "docx", "xlsx", "txt"])
    
    disciplinas_obrigatorias = st.select_slider("Disciplinas obrigatórias *", options=opcoes_progresso)
    desenvolvimento_do_projeto = st.select_slider("Desenvolvimento do projeto/pesquisa *", options=opcoes_progresso)
    revisao_de_literatura = st.select_slider("Revisão de literatura *", options=opcoes_progresso)
    coleta_de_dados = st.select_slider("Coleta de dados *", options=opcoes_progresso)
    analise_de_dados = st.select_slider("Análise de dados *", options=opcoes_progresso)
    escrita_cientifica = st.select_slider("Escrita científica (artigo/dissertação/tese) *", options=opcoes_progresso)

    st.markdown("---")
    st.subheader("BLOCO 2 - Organização e prazos")
    estou_conseguindo_cumprir = st.radio("Estou conseguindo cumprir meus prazos *", list(opcoes_organizacao.keys()))
    rotina_estudos_organizada = st.radio("Minha rotina de estudos está organizada *", list(opcoes_organizacao.keys()))
    equilibrar_demandas = st.radio("Estou conseguindo equilibrar demandas acadêmicas *", list(opcoes_organizacao.keys()))

    st.markdown("---")
    st.subheader("BLOCO 3 - Orientação e suporte")
    satisfeito_orientacao = st.radio("Estou satisfeito com a orientação recebida *", list(opcoes_suporte.keys()))
    sinto_suporte_programa = st.radio("Sinto que tenho suporte do programa *", list(opcoes_suporte.keys()))
    clareza_proximos_passos = st.radio("Tenho clareza sobre os próximos passos da pesquisa *", list(opcoes_suporte.keys()))

    st.markdown("---")
    st.subheader("BLOCO 4 - Produtividade percebida")
    avalia_produtividade = st.radio("Como você avalia sua produtividade na última semana? *", list(opcoes_produtividade.keys()))

    st.markdown("---")
    st.subheader("BLOCO 5 - Risco acadêmico")
    sente_que_esta_atrasado = st.radio("Você sente que está atrasado(a) no cronograma?", list(opcoes_atrasado.keys()))

    # --- INSTRUMENTO 2: Como se sente hoje ---
    st.markdown("---")
    st.header("🧠 Como se sente hoje")
    
    por_que_se_sente_bem = st.radio("Você parece estar bem no momento. Continue cuidando da sua rotina. Gostaria de compartilhar o por que se sente bem? *", ["Sim", "Não"])
    alguns_sinais_de_estresse = st.text_area("Alguns sinais de estresse apareceram. Vale a pena observar e cuidar de você. Como você explica esse sentimento? Como podemos te ajudar? *")

    st.write("**Como se sente (Selecione todas as opções aplicáveis) *:**")
    
    checkbox_labels = [
        "estressado(a)", "cansado(a)", "sobrecarregado(a)", "ansioso(a)", "triste",
        "desmotivado(a)", "sem perspectiva", "irritado(a)", "preocupado(a)", "solitário(a)",
        "doente", "com dificuldade para dormir", "dificuldade de concentração",
        "pressão acadêmica/profissional", "muitos compromissos", "problemas pessoais",
        "conflitos familiares ou interpessoais", "dificuldades financeiras",
        "sinto que não sou capaz", "dificuldade em conciliar trabalho, estudo e vida pessoal"
    ]
    
    check_choices = []
    for label in checkbox_labels:
        check_choices.append(st.checkbox(label))

    gostaria_de_falar_um_pouco = st.text_area("Gostaria de falar um pouco mais? Como podemos te ajudar? *")

    # Botão de submissão do formulário (Voltará a aparecer agora que o código compila limpo)
    submetido = st.form_submit_button("Enviar Dados para o REDCap")

# Processamento pós-clique na camada lógica de submissão
if submetido:
    if not record_id:
        st.error("O campo **Record ID** é obrigatório.")
    elif arquivo_cronograma is None:
        st.error("O upload do **cronograma** é obrigatório.")
    else:
        with st.spinner("Enviando dados estruturados e arquivos anexos para o REDCap HCFMB..."):
            
            # Convertendo os textos selecionados nas barras para as strings equivalentes do REDCap usando o dicionário reverso
            dados_formulario = {
                "record_id": record_id,
                "data_e_horario": data_envio_redcap,
                "horario": horario_atual,
                "andamento_academico": mapa_valores_redcap[andamento_academico],
                "disciplinas_obrigatorias": mapa_valores_redcap[disciplinas_obrigatorias],
                "desenvolvimento_do_projeto": mapa_valores_redcap[desenvolvimento_do_projeto],
                "revisao_de_literatura": mapa_valores_redcap[revisao_de_literatura],
                "coleta_de_dados": mapa_valores_redcap[coleta_de_dados],
                "analise_de_dados": mapa_valores_redcap[analise_de_dados],
                "escrita_cientifica": mapa_valores_redcap[escrita_cientifica],
                "estou_conseguindo_cumprir": opcoes_organizacao[estou_conseguindo_cumprir],
                "rotina_estudos_organizada": opcoes_organizacao[rotina_estudos_organizada],
                "equilibrar_demandas": opcoes_organizacao[equilibrar_demandas],
                "satisfeito_orientacao": opcoes_suporte[satisfeito_orientacao],
                "sinto_suporte_programa": opcoes_suporte[sinto_suporte_programa],
                "clareza_proximos_passos": opcoes_suporte[clareza_proximos_passos],
                "avalia_produtividade": opcoes_produtividade[avalia_produtividade],
                "sente_que_esta_atrasado": opcoes_atrasado[sente_que_esta_atrasado],
                "check_in_progresso_pos_graduacao_complete": "2",
                "por_que_se_sente_bem": "1" if por_que_se_sente_bem == "Sim" else "0",
                "alguns_sinais_de_estresse": alguns_sinais_de_estresse,
                "gostaria_de_falar_um_pouco": gostaria_de_falar_um_pouco,
                "como_se_sente_hoje_complete": "2"
            }
            
            # Vinculando as checkboxes dinamicamente
            for idx, checked in enumerate(check_choices, start=1):
                dados_formulario[f"como_se_sente___{idx}"] = "1" if checked else "0"

            try:
                # Transação 1: Upload de registros e variáveis textuais
                response = project.import_records([dados_formulario])
                
                # Transação 2: Upload binário do arquivo
                project.import_file(
                    record=record_id,
                    field="envie_aqui_seu_cronograma",
                    file_name=arquivo_cronograma.name,
                    file_object=arquivo_cronograma
                )
                
                st.success(f"🎉 Registro '{record_id}' e arquivo salvos com sucesso no servidor REDCap HCFMB!")
                
            except Exception as e:
                st.error(f"Falha de gravação ou upload de documento na API do REDCap: {e}")