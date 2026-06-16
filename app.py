import streamlit as st
from redcap import Project
import requests
from datetime import datetime
import json

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

# Inicialização das variáveis de controle de sessão do Streamlit
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "dados_usuario" not in st.session_state:
    st.session_state.dados_usuario = {}

# Lista de opções para as barras horizontais
opcoes_progresso = [
    "Selecione...",
    "0% → Não iniciei",
    "25% → Início",
    "50% → Em andamento",
    "75% → Quase finalizado",
    "100% → Concluído"
]

# Dicionários de mapeamento (Visualização <-> Banco de Dados)
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

# Lista de rótulos das checkboxes de sentimentos
checkbox_labels = [
    "estressado(a)", "cansado(a)", "sobrecarregado(a)", "ansioso(a)", "triste",
    "desmotivado(a)", "sem perspectiva", "irritado(a)", "preocupado(a)", "solitário(a)",
    "doente", "com dificuldade para dormir", "dificuldade de concentração",
    "pressão acadêmica/profissional", "muitos compromissos", "problemas pessoais",
    "conflitos familiares ou interpessoais", "dificuldades financeiras",
    "sinto que não sou capaz", "dificuldade em conciliar trabalho, estudo e vida pessoal"
]

# =============================================================================
# FLUXO 1: TELA DE LOGIN
# =============================================================================
if not st.session_state.autenticado:
    st.title("🔐 Login - Acompanhamento de Pós-Graduação")
    st.write("Por favor, insira suas credenciais institucionais para acessar seu painel.")
    
    with st.form("form_login"):
        input_usuario = st.text_input("Usuário / Login")
        input_senha = st.text_input("Senha", type="password")
        btn_login = st.form_submit_button("Entrar")
        
    if btn_login:
        if not input_usuario or not input_senha:
            st.error("Por favor, preencha ambos os campos de login e senha.")
        else:
            with st.spinner("Autenticando e extraindo histórico completo..."):
                try:
                    # Exporta TODOS os campos do projeto para fazer o carregamento integral
                    registros = project.export_records()
                    
                    login_sucesso = False
                    for reg in registros:
                        if reg.get('login') == input_usuario and reg.get('senha') == input_senha:
                            st.session_state.autenticado = True
                            # Armazena o dicionário completo do REDCap na sessão
                            st.session_state.dados_usuario = reg
                            login_sucesso = True
                            break
                    
                    if login_sucesso:
                        st.success("Histórico carregado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos. Verifique suas credenciais.")
                        
                except Exception as e:
                    st.error(f"Erro ao conectar com o serviço de autenticação: {e}")

# =============================================================================
# FLUXO 2: FORMULÁRIO PRINCIPAL (Liberado pós-autenticação com dados carregados)
# =============================================================================
else:
    # Atalho para o dicionário de dados do usuário logado
    u_dados = st.session_state.dados_usuario

    col_titulo, col_logout = st.columns([5, 1])
    with col_titulo:
        st.title("🎓 Sistema de Acompanhamento")
    with col_logout:
        if st.button("Sair 🚪"):
            st.session_state.autenticado = False
            st.session_state.dados_usuario = {}
            st.rerun()

    st.write(f"Olá, **{u_dados.get('nome', 'Discente')}**! Abaixo estão os seus dados consolidados no último check-in.")

    tab_pessoais, tab_progresso, tab_sentimentos = st.tabs([
        "👤 1. Dados Pessoais", 
        "📊 2. Progresso Acadêmico", 
        "🧠 3. Como se Sente Hoje"
    ])

    with st.form("form_redcap_abas", clear_on_submit=False):
        
        # --- ABA 1: DADOS PESSOAIS ---
        with tab_pessoais:
            st.header("👤 Identificação do Aluno")
            st.info(f"**Seu RA autenticado:** {u_dados.get('ra', '')}")
            
            nome = st.text_input("Nome Completo", value=u_dados.get('nome', ''))
            e_mail = st.text_input("E-mail Institucional", value=u_dados.get('e_mail', ''))
            
        # --- ABA 2: PROGRESSO ACADÊMICO ---
        with tab_progresso:
            st.header("📊 Check-In Progresso Pós-Graduação")
            
            # Resgate e conversão segura de data e hora do banco
            db_data = u_dados.get('data_e_horario', '')
            init_data = datetime.strptime(db_data, "%Y-%m-%d").date() if db_data else None
            
            db_hora = u_dados.get('horario', '')
            init_hora = datetime.strptime(db_hora, "%H:%M").time() if db_hora else None

            data_selecionada = st.date_input("Data de registro", value=init_data, format="DD/MM/YYYY")
            horario_selecionado = st.time_input("Horário de registro", value=init_hora)
            st.markdown("---")
            
            st.subheader("BLOCO 1 - Andamento Acadêmico")
            
            # Mapeamento dinâmico dos Sliders com base no banco de dados
            andamento_academico = st.select_slider("Andamento Acadêmico", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('andamento_academico'), "Selecione..."), key="s_andamento")
            
            arquivo_cronograma = st.file_uploader("Envie aqui seu cronograma (PDF, DOCX, etc.)", type=["pdf", "docx", "xlsx", "txt"])
            if u_dados.get('envie_aqui_seu_cronograma'):
                st.caption(f"📁 Um cronograma já se encontra anexado ao seu perfil no REDCap.")
            
            disciplinas_obrigatorias = st.select_slider("Disciplinas obrigatórias", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('disciplinas_obrigatorias'), "Selecione..."), key="s_disc")
            desenvolvimento_do_projeto = st.select_slider("Desenvolvimento do projeto/pesquisa", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('desenvolvimento_do_projeto'), "Selecione..."), key="s_desenv")
            revisao_de_literatura = st.select_slider("Revisão de literatura", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('revisao_de_literatura'), "Selecione..."), key="s_rev")
            coleta_de_dados = st.select_slider("Coleta de dados", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('coleta_de_dados'), "Selecione..."), key="s_coleta")
            analise_de_dados = st.select_slider("Análise de dados", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('analise_de_dados'), "Selecione..."), key="s_analise")
            escrita_cientifica = st.select_slider("Escrita científica (artigo/dissertação/tese)", options=opcoes_progresso, value=mapa_reverso_progresso.get(u_dados.get('escrita_cientifica'), "Selecione..."), key="s_escrita")

            st.markdown("---")
            st.subheader("BLOCO 2 - Organização e prazos")
            
            # Resgate dos Radio Buttons calculando o índice salvo
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
            
            por_que_se_sente_bem = st.radio(
                "Você parece estar bem no momento. Continue cuidando da sua rotina. Gostaria de compartilhar o por que se sente bem?", 
                ["Sim", "Não"], index=idx_bem
            )
            
            descreva_como_se_sente = ""
            alguns_sinais_de_estresse = ""
            check_choices = [False] * 20
            
            if por_que_se_sente_bem == "Sim":
                st.markdown("#### Detalhes sobre seus sentimentos")
                descreva_como_se_sente = st.text_area("Descreva como se sente:", value=u_dados.get('descreva_como_se_sente', ''))
                alguns_sinais_de_estresse = st.text_area("Alguns sinais de estresse apareceram. Vale a pena observar e cuidar de você. Como você explica esse sentimento? Como podemos te ajudar?", value=u_dados.get('alguns_sinais_de_estresse', ''))

                st.write("**Como se sente (Selecione as opções aplicáveis):**")
                
                check_choices = []
                for idx, label in enumerate(checkbox_labels, start=1):
                    # Puxa o status booleano (True/False) salvo para as checkboxes dinâmicas como_se_sente___x
                    db_checked = u_dados.get(f"como_se_sente___{idx}") == "1"
                    check_choices.append(st.checkbox(label, value=db_checked))

            st.markdown("---")
            gostaria_de_falar_um_pouco = st.text_area("Gostaria de falar um pouco mais? Como podemos te ajudar?", value=u_dados.get('gostaria_de_falar_um_pouco', ''))

        submetido = st.form_submit_button("Atualizar Meu Formulário Completo")

    # Processamento e persistência das modificações
    if submetido:
        with st.spinner("Sincronizando modificações no seu perfil do REDCap..."):
            
            data_envio = data_selecionada.strftime("%Y-%m-%d") if data_selecionada else ""
            horario_envio = horario_selecionado.strftime("%H:%M") if horario_selecionado else ""
            
            dados_formulario = {
                "record_id": u_dados.get('record_id'),  
                "ra": u_dados.get('ra'),
                "nome": nome,
                "e_mail": e_mail,
                "login": u_dados.get('login'),
                "senha": u_dados.get('senha'),
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

            try:
                # Transação 1: Gravação das atualizações estruturadas
                project.import_records([dados_formulario])
                
                # Atualiza os dados na memória da sessão para manter a tela sincronizada pós-clique
                st.session_state.dados_usuario.update(dados_formulario)
                
                # Transação 2: Atualização do arquivo se um novo upload foi efetuado
                if arquivo_cronograma is not None:
                    project.import_file(
                        record=str(u_dados.get('record_id')),
                        field="envie_aqui_seu_cronograma",
                        file_name=arquivo_cronograma.name,
                        file_object=arquivo_cronograma
                    )
                st.success("🎉 Seus dados e avaliações foram sincronizados com sucesso!")
                st.rerun()
                    
            except Exception as e:
                st.error(f"Erro ao salvar modificações no perfil: {e}")