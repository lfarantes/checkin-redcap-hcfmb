import streamlit as st
from redcap import Project
import requests
from datetime import datetime
import json
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(page_title="Check-in Pós-Graduação", page_icon="🎓", layout="wide")

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

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "dados_usuario" not in st.session_state:
    st.session_state.dados_usuario = {}

opcoes_progresso = [
    "Selecione...", "0% → Não iniciei", "25% → Início", 
    "50% → Em andamento", "75% → Quase finalizado", "100% → Concluído"
]

mapa_valores_redcap = {
    "0% → Não iniciei": "0", "25% → Início": "25", "50% → Em andamento": "50", 
    "75% → Quase finalizado": "75", "100% → Concluído": "100"
}
mapa_reverso_progresso = {v: k for k, v in mapa_valores_redcap.items()}

opcoes_organizacao = {"Nada organizado": "0", "Pouco": "1", "Moderado": "2", "Bem-organizado": "3"}
mapa_reverso_organizacao = {v: k for k, v in opcoes_organizacao.items()}

opcoes_suporte = {"Muito insatisfeito": "0", "Insatisfeito": "1", "Satisfeito": "2", "Muito satisfeito": "3"}
mapa_reverso_suporte = {v: k for k, v in opcoes_suporte.items()}

opcoes_produtividade = {"Baixa": "1", "Moderada": "2", "Alta": "3"}
mapa_reverso_produtividade = {v: k for k, v in opcoes_produtividade.items()}

opcoes_atrasado = {"Não": "1", "Um pouco": "2", "Sim": "3"}
mapa_reverso_atrasado = {v: k for k, v in opcoes_atrasado.items()}

atividades_cronograma = [
    "Revisão bibliográfica", "Capacitação em ultrassonografia", "Elaboração/ajustes do projeto",
    "Aprovação ética (CEP)", "Coleta de dados", "Organização do banco de dados",
    "Análises preliminares", "Análise estatística final", "Interpretação dos resultados",
    "Redação do artigo científico", "Redação da tese", "Revisão com orientador",
    "Submissão do artigo"
]

# Semestres mapeados sequencialmente (Mapeamento padrão máximo de 10 semestres)
lista_semestres_padrao = [
    {"rotulo": "2025 - 1ºS", "ano": 2025, "semestre": 1},
    {"rotulo": "2025 - 2ºS", "ano": 2025, "semestre": 2},
    {"rotulo": "2026 - 1ºS", "ano": 2026, "semestre": 1},
    {"rotulo": "2026 - 2ºS", "ano": 2026, "semestre": 2},
    {"rotulo": "2027 - 1ºS", "ano": 2027, "semestre": 1},
    {"rotulo": "2027 - 2ºS", "ano": 2027, "semestre": 2},
    {"rotulo": "2028 - 1ºS", "ano": 2028, "semestre": 1},
    {"rotulo": "2028 - 2ºS", "ano": 2028, "semestre": 2},
    {"rotulo": "2029 - 1ºS", "ano": 2029, "semestre": 1},
    {"rotulo": "2029 - 2ºS", "ano": 2029, "semestre": 2}
]

checkbox_labels = [
    "estressado(a)", "cansado(a)", "sobrecarregado(a)", "ansioso(a)", "triste",
    "desmotivado(a)", "sem perspectiva", "irritado(a)", "preocupado(a)", "solitário(a)",
    "doente", "com dificuldade para dormir", "dificuldade de concentração",
    "pressão acadêmica/profissional", "muitos compromissos", "problemas pessoais",
    "conflitos familiares ou interpessoais", "dificuldades financeiras",
    "sinto que não sou capable", "dificuldade em conciliar trabalho estudo e vida pessoal"
]

# Lógica auxiliar para determinar se um semestre está contido no intervalo de datas do aluno
def semestre_no_intervalo(ano_semestre, data_ini, data_fim):
    if not data_ini or not data_fim:
        return True # Fallback para exibir tudo caso não informe datas
    
    # Define datas fictícias no meio de cada semestre para checagem simples
    data_referencia = datetime(ano_semestre["ano"], 5, 1).date() if ano_semestre["semestre"] == 1 else datetime(ano_semestre["ano"], 11, 1).date()
    return data_ini <= data_referencia <= data_fim

# =============================================================================
# FLUXO 1: TELA DE LOGIN
# =============================================================================
if not st.session_state.autenticado:
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.title("🔐 Login - Check-in Pós-Graduação")
        with st.form("form_login"):
            input_usuario = st.text_input("Usuário / Login")
            input_senha = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("Entrar")
            
        if btn_login:
            if not input_usuario or not input_senha:
                st.error("Por favor, preencha ambos os campos.")
            else:
                with st.spinner("Autenticando..."):
                    try:
                        registros = project.export_records()
                        login_sucesso = False
                        for reg in registros:
                            if reg.get('login') == input_usuario and reg.get('senha') == input_senha:
                                st.session_state.autenticado = True
                                st.session_state.dados_usuario = reg
                                login_sucesso = True
                                break
                        if login_sucesso:
                            st.rerun()
                        else:
                            st.error("Credenciais inválidas.")
                    except Exception as e:
                        st.error(f"Erro na conexão: {e}")

# =============================================================================
# FLUXO 2: FORMULÁRIO PRINCIPAL
# =============================================================================
else:
    u_dados = st.session_state.dados_usuario

    col_titulo, col_logout = st.columns([5, 1])
    with col_titulo:
        st.title("🎓 Sistema de Acompanhamento - UNESP")
    with col_logout:
        if st.button("Sair 🚪", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.dados_usuario = {}
            st.rerun()

    tab_pessoais, tab_progresso, tab_sentimentos, tab_cronograma = st.tabs([
        "👤 1. Dados Pessoais", 
        "📊 2. Progresso Acadêmico", 
        "🧠 3. Como se Sente Hoje",
        "📅 4. Meu Cronograma"
    ])

    with st.form("form_redcap_abas", clear_on_submit=False):
        
        # --- ABA 1: DADOS PESSOAIS ---
        with tab_pessoais:
            st.header("👤 Identificação do Aluno")
            st.info(f"**Seu RA autenticado:** {u_dados.get('ra', '')}")
            
            nome = st.text_input("Nome Completo", value=u_dados.get('nome', ''))
            e_mail = st.text_input("E-mail Institucional", value=u_dados.get('e_mail', ''))
            
            st.markdown("---")
            st.subheader("🗓️ Vigência do seu Programa de Pós-Graduação")
            st.caption("Insira os dados abaixo para que o cronograma ajuste automaticamente o número de semestres da sua matriz.")
            
            # Resgate das novas variáveis do REDCap
            db_ini_pos = u_dados.get('data_inicio_pos', '')
            init_ini_pos = datetime.strptime(db_ini_pos, "%Y-%m-%d").date() if db_ini_pos else None
            
            db_fim_pos = u_dados.get('data_fim_pos', '')
            init_fim_pos = datetime.strptime(db_fim_pos, "%Y-%m-%d").date() if db_fim_pos else None

            data_inicio_pos = st.date_input("Data de Início da Pós-Graduação", value=init_ini_pos, format="DD/MM/YYYY")
            data_fim_pos = st.date_input("Data Prevista de Defesa", value=init_fim_pos, format="DD/MM/YYYY")
            
        # --- ABA 2: PROGRESSO ACADÊMICO ---
        with tab_progresso:
            st.header("📊 Check-In Progresso Pós-Graduação")
            db_data = u_dados.get('data_e_horario', '')
            init_data = datetime.strptime(db_data, "%Y-%m-%d").date() if db_data else None
            db_hora = u_dados.get('horario', '')
            init_hora = datetime.strptime(db_hora, "%H:%M").time() if db_hora else None

            data_selecionada = st.date_input("Data de registro", value=init_data, format="DD/MM/YYYY")
            horario_selecionado = st.time_input("Horário de registro", value=init_hora)
            st.markdown("---")
            
            st.subheader("BLOCO 1 - Andamento Acadêmico")
            andamento_academico = st.select_slider("Andamento Acadêmico", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('andamento_academico'), "Selecione..."), key="s_andamento")
            arquivo_cronograma = st.file_uploader("Envie aqui seu arquivo complementar (Opcional)", type=["pdf", "docx", "xlsx", "txt"])
            
            disciplinas_obrigatorias = st.select_slider("Disciplinas obrigatórias", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('disciplinas_obrigatorias'), "Selecione..."), key="s_disc")
            desenvolvimento_do_projeto = st.select_slider("Desenvolvimento do projeto/pesquisa", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('desenvolvimento_do_projeto'), "Selecione..."), key="s_desenv")
            revisao_de_literatura = st.select_slider("Revisão de literatura", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('revisao_de_literatura'), "Selecione..."), key="s_rev")
            coleta_de_dados = st.select_slider("Coleta de dados", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('coleta_de_dados'), "Selecione..."), key="s_coleta")
            analise_de_dados = st.select_slider("Análise de dados", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('analise_de_dados'), "Selecione..."), key="s_analise")
            escrita_cientifica = st.select_slider("Escrita científica (artigo/dissertação/tese)", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('escrita_cientifica'), "Selecione..."), key="s_escrita")

            st.markdown("---")
            st.subheader("BLOCO 2 - Organização e prazos")
            list_org = list(opcoes_organizacao.keys())
            idx_cumprir = list_org.index(mapa_reverso_organizacao[u_dados.get('estou_conseguindo_cumprir')]) if u_dados.get('estou_conseguindo_cumprir') in mapa_reverso_organizacao else None
            idx_rotina = list_org.index(mapa_reverso_organizacao[u_dados.get('rotina_estudos_organizada')]) if u_dados.get('rotina_estudos_organizada') in mapa_reverso_organizacao else None
            idx_demandas = list_org.index(mapa_reverso_organizacao[u_dados.get('equilibrar_demandas')]) if u_dados.get('equilibrar_demandas') in mapa_reverso_organizacao else None

            estou_conseguindo_cumprir = st.radio("Estou conseguindo cumprir meus prazos", list_org, index=idx_cumprir)
            rotina_estudos_organizada = st.radio("Minha rotina de estudos está organizada", list_org, index=idx_rotina)
            equilibrar_demandas = st.radio("Estou conseguindo equilibrar demandas acadêmicas", list_org, index=idx_demandas)

            st.markdown("---")
            st.subheader("BLOCO 3 - Orientação e suporte")
            list_sup = list(opcoes_suporte.keys())
            idx_orientacao = list_sup.index(mapa_reverso_suporte[u_dados.get('satisfeito_orientacao')]) if u_dados.get('satisfeito_orientacao') in mapa_reverso_suporte else None
            idx_suporte = list_sup.index(mapa_reverso_suporte[u_dados.get('sinto_suporte_programa')]) if u_dados.get('sinto_suporte_programa') in mapa_reverso_suporte else None
            idx_passos = list_sup.index(mapa_reverso_suporte[u_dados.get('clareza_proximos_passos')]) if u_dados.get('clareza_proximos_passos') in mapa_reverso_suporte else None

            satisfeito_orientacao = st.radio("Estou satisfeito com a orientação recebida", list_sup, index=idx_orientacao)
            sinto_suporte_programa = st.radio("Sinto que tenho suporte do programa", list_sup, index=idx_suporte)
            clareza_proximos_passos = st.radio("Tenho clareza sobre os próximos passos da pesquisa", list_sup, index=idx_passos)

            st.markdown("---")
            st.subheader("BLOCO 4 - Produtividade percebida")
            list_prod = list(opcoes_produtividade.keys())
            idx_prod = list_prod.index(mapa_reverso_produtividade[u_dados.get('avalia_produtividade')]) if u_dados.get('avalia_produtividade') in mapa_reverso_produtividade else None
            avalia_produtividade = st.radio("Como você avalia sua produtividade na última semana?", list_prod, index=idx_prod)

            st.markdown("---")
            st.subheader("BLOCO 5 - Risco acadêmico")
            list_risco = list(opcoes_atrasado.keys())
            idx_risco = list_risco.index(mapa_reverso_atrasado[u_dados.get('sente_que_esta_atrasado')]) if u_dados.get('sente_que_esta_atrasado') in mapa_reverso_atrasado else None
            sente_que_esta_atrasado = st.radio("Você sente que está atrasado(a) no cronograma?", list_risco, index=idx_risco)

        # --- ABA 3: COMO SE SENTE HOJE ---
        with tab_sentimentos:
            st.header("🧠 Como se sente hoje")
            db_bem = u_dados.get('por_que_se_sente_bem', '')
            idx_bem = 0 if db_bem == "1" else (1 if db_bem == "0" else None)
            por_que_se_sente_bem = st.radio("Gostaria de compartilhar o por que se sente bem?", ["Sim", "Não"], index=idx_bem)
            
            descreva_como_se_sente = ""
            alguns_sinais_de_estresse = ""
            check_choices = [False] * 20
            
            if por_que_se_sente_bem == "Sim":
                descreva_como_se_sente = st.text_area("Descreva como se sente:", value=u_dados.get('descreva_como_se_sente', ''))
                alguns_sinais_de_estresse = st.text_area("Alguns sinais de estresse apareceram. Como podemos te ajudar?", value=u_dados.get('alguns_sinais_de_estresse', ''))
                st.write("**Como se sente:**")
                check_choices = []
                for idx, label in enumerate(checkbox_labels, start=1):
                    db_checked = u_dados.get(f"como_se_sente___{idx}") == "1"
                    check_choices.append(st.checkbox(label, value=db_checked))

            st.markdown("---")
            gostaria_de_falar_um_pouco = st.text_area("Gostaria de falar um pouco mais?", value=u_dados.get('gostaria_de_falar_um_pouco', ''))

        # --- ABA 4: CRONOGRAMA INTELIGENTE E DINÂMICO ---
        with tab_cronograma:
            st.header("📅 Matriz de Planejamento e Execução Personalizada")
            
            # Filtra dinamicamente as colunas com base no período letivo real do aluno
            semestres_ativos = [s for s in lista_semestres_padrao if semestre_no_intervalo(s, data_inicio_pos, data_fim_pos)]
            colunas_ativas_rotulos = [s["rotulo"] for s in semestres_ativos]
            
            if not semestres_ativos:
                st.warning("⚠️ Selecione as datas de início e defesa corretas na Aba 1 para gerar a matriz do seu cronograma.")
                df_cronograma = pd.DataFrame(columns=["Atividade"])
            else:
                st.write(f"Sua pós-graduação está programada para durar **{len(semestres_ativos)} semestres**. Marque abaixo suas metas:")
                
                matriz_dados = []
                for a_idx, atividade in enumerate(atividades_cronograma, start=1):
                    linha = {"Atividade": atividade}
                    for sem in semestres_ativos:
                        # Localiza a posição do semestre no mapeamento absoluto (1 a 10) do REDCap
                        posicao_absoluta_redcap = lista_semestres_padrao.index(sem) + 1
                        chave_checkbox = f"cronograma_a{a_idx}_c1___{posicao_absoluta_redcap}"
                        linha[sem["rotulo"]] = u_dados.get(chave_checkbox) == "1"
                    matriz_dados.append(linha)
                    
                df_cronograma = pd.DataFrame(matriz_dados)
            
            cronograma_editado = st.data_editor(
                df_cronograma,
                hide_index=True,
                disabled=["Atividade"],
                use_container_width=True
            )

        submetido = st.form_submit_button("Atualizar Todo o Meu Formulário e Cronograma")

    # Processamento pós-submissão
    if submetido:
        with st.spinner("Sincronizando check-in..."):
            
            data_envio = data_selecionada.strftime("%Y-%m-%d") if data_selecionada else ""
            horario_envio = horario_selecionado.strftime("%H:%M") if horario_selecionado else ""
            
            ini_pos_envio = data_inicio_pos.strftime("%Y-%m-%d") if data_inicio_pos else ""
            fim_pos_envio = data_fim_pos.strftime("%Y-%m-%d") if data_fim_pos else ""
            
            dados_formulario = {
                "record_id": u_dados.get('record_id'),  
                "ra": u_dados.get('ra'),
                "nome": nome,
                "e_mail": e_mail,
                "login": u_dados.get('login'),
                "senha": u_dados.get('senha'),
                "data_inicio_pos": ini_pos_envio,  # <--- NOVOS CAMPOS SALVOS
                "data_fim_pos": fim_pos_envio,      # <--- NOVOS CAMPOS SALVOS
                "dados_pessoais_complete": "2" if (nome or e_mail) else "0",  
                
                "data_e_horario": data_envio,
                "horario": horario_envio,
                "andamento_academico": mapa_valores_redcap[andamento_academico] if andamento_academico != "Selecione..." else "",
                "disciplinas_obrigatorias": mapa_valores_redcap[disciplinas_obrigatorias] if disciplinas_obrigatorias != "Selecione..." else "",
                "desenvolvimento_do_projeto": mapa_valores_redcap[desenvolvimento_do_projeto] if desenvolvimento_do_projeto != "Selecione..." else "",
                "revisao_de_literatura": mapa_valores_redcap[revisao_de_literatura] if revisao_de_literatura != "Selecione..." else "",
                "coleta_de_dados": mapa_valores_redcap[coleta_de_dados] if coleta_de_dados != "Selecione..." else "",
                "analise_de_dados": mapa_valores_redcap[analise_de_dados] if analise_de_dados != "Selecione..." else "",
                "escrita_cientifica": mapa_valores_redcap[escrita_cientifica] if escrita_cientifica != "Selecione..." else "",
                "estou_conseguindo_cumprir": opcoes_organizacao[estou_conseguindo_cumprir] if estou_conseguindo_cumprir else "",
                "rotina_estudos_organizada": opcoes_organizacao[rotina_estudos_organizada] if rotina_estudos_organizada else "",
                "equilibrar_demandas": opcoes_organizacao[equilibrar_demandas] if equilibrar_demandas else "",
                "satisfeito_orientacao": opcoes_suporte[satisfeito_orientacao] if satisfeito_orientacao else "",
                "sinto_suporte_programa": opcoes_suporte[sinto_suporte_programa] if sinto_suporte_programa else "",
                "clareza_proximos_passos": opcoes_suporte[clareza_proximos_passos] if clareza_proximos_passos else "",
                "avalia_produtividade": opcoes_produtividade[avalia_produtividade] if avalia_produtividade else "",
                "sente_que_esta_atrasado": opcoes_atrasado[sente_que_esta_atrasado] if sente_que_esta_atrasado else "",
                "check_in_progresso_pos_graduacao_complete": "2",  
                
                "por_que_se_sente_bem": "1" if por_que_se_sente_bem == "Sim" else ("0" if por_que_se_sente_bem == "Não" else ""),
                "descreva_como_se_sente": descreva_como_se_sente,
                "alguns_sinais_de_estresse": alguns_sinais_de_estresse,
                "gostaria_de_falar_um_pouco": gostaria_de_falar_um_pouco,
                "como_se_sente_hoje_complete": "2" if por_que_se_sente_bem else "0"  
            }
            
            for idx, checked in enumerate(check_choices, start=1):
                dados_formulario[f"como_se_sente___{idx}"] = "1" if checked else "0"

            # Gravação condicional apenas das checkboxes que estão visíveis na tela ativa do aluno
            if semestres_ativos:
                for r_idx, row in cronograma_editado.iterrows():
                    for sem in semestres_ativos:
                        posicao_absoluta_redcap = lista_semestres_padrao.index(sem) + 1
                        valor_bool = row[sem["rotulo"]]
                        dados_formulario[f"cronograma_a{r_idx+1}_c1___{posicao_absoluta_redcap}"] = "1" if valor_bool else "0"

            try:
                project.import_records([dados_formulario])
                st.session_state.dados_usuario.update(dados_formulario)
                
                if arquivo_cronograma is not None:
                    project.import_file(
                        record=str(u_dados.get('record_id')),
                        field="envie_aqui_seu_cronograma",
                        file_name=arquivo_cronograma.name,
                        file_object=arquivo_cronograma
                    )
                st.success("🎉 Perfil e cronograma dinâmico atualizados com sucesso!")
                st.rerun()
                    
            except Exception as e:
                st.error(f"Erro ao salvar dados: {e}")