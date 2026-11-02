import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io, os
import json, gspread    
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv



@st.cache_resource
def conectar_planilha():

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

    client = gspread.authorize(creds)

    return client.open(
        "RSVP Marina e Vitória"
    ).worksheet(
        "Confirmacoes"
    )


# ==========================================
# CONFIGURAÇÕES
# ==========================================

st.set_page_config(
    page_title="Aniversário Marina e Vitória",
    page_icon="🎉",
    layout="wide"
)

st.markdown("""
<style>

.stApp{
    background-color:#FCE4EC;
}

/* Sidebar */
[data-testid="stSidebar"]{
    background-color:#F8BBD0;
}

/* Força texto escuro */
.stApp,
.stApp p,
.stApp label,
.stApp span,
.stApp div {
    color:#333333;
}

/* Força títulos */
h1,
h2,
h3,
h4,
h5,
h6 {
    color:#C2185B !important;
}

/* Subheaders do Streamlit */
[data-testid="stHeading"] {
    color:#C2185B !important;
}

/* Labels dos inputs */
[data-testid="stWidgetLabel"] {
    color:#333333 !important;
}

</style>
""", unsafe_allow_html=True)

LIMITE_VAGAS = 300

import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_USUARIO = os.getenv("ADMIN_USER")
ADMIN_SENHA = os.getenv("ADMIN_PASSWORD")





# ==========================================
# FUNÇÕES
# ==========================================

def salvar_confirmacao(
        responsavel,
        presenca,
        participantes
):

    sheet = conectar_planilha()

    data = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    linhas = []

    for participante in participantes:

        linhas.append([
            data,
            responsavel,
            presenca,
            participante["nome"],
            participante["faixa"]
        ])

    sheet.append_rows(linhas)


def total_participantes_confirmados():

    query = """
    SELECT COUNT(*)
    FROM participantes p
    INNER JOIN confirmacoes c
    ON p.confirmacao_id = c.id
    WHERE c.presenca='Sim'
    """

    return pd.read_sql(query, conn).iloc[0, 0]


def carregar_dashboard():

    participantes_df = carregar_participantes()

    if participantes_df.empty:
        return pd.DataFrame()

    return (
        participantes_df
        .groupby(
            [
                "responsavel",
                "presenca",
                "data"
            ]
        )
        .size()
        .reset_index(name="quantidade")
    )


def carregar_participantes():

    sheet = conectar_planilha()

    dados = sheet.get_all_records()

    if not dados:

        return pd.DataFrame(
            columns=[
                "data",
                "responsavel",
                "presenca",
                "nome",
                "faixa"
            ]
        )

    return pd.DataFrame(dados)

# ==========================================
# MENU
# ==========================================

pagina = st.sidebar.radio(
    "Menu",
    [
        "Evento",
        "Administração"
    ]
)

# ==========================================
# EVENTO
# ==========================================

if pagina == "Evento":

    st.title("🎉 ANIVERSÁRIO MARINA E VITÓRIA")

    # FOTO + INFORMAÇÕES
    col_foto, col_info = st.columns([1, 2])

    with col_foto:
        st.image(
            "images/foto_capa.png",
            width=200
        )

    with col_info:

        st.markdown("## 💖 Nossa Festa")

        st.markdown("""
        ### Informações do Evento

        📅 **Data:** 20/11/2026

        🕗 **Horário:** 16h

        📍 **Local:** Rua Carijós, 906 - Vila Alzira

        🍽️ **Aniversário Marina e Vitória**
        """)

    # Espaçamento
    st.markdown("<br>", unsafe_allow_html=True)

    # FORMULÁRIO CENTRALIZADO
    col_esq, col_form, col_dir = st.columns([1, 2, 1])

    with col_form:

        st.divider()

        st.subheader("✅ Confirmação de Presença")

        responsavel = st.text_input(
            "Nome do responsável"
        )
        faixa_responsavel = st.selectbox(
            "Faixa etária do responsável",
            [
                "Menor de 5 anos",
                "Entre 5 e 12 anos",
                "Maior de 12 anos"
            ]
        )


        presenca = st.radio(
            "Você irá ao evento?",
            ["Sim", "Não"],
            horizontal=True
        )

        st.write("Acompanhantes (crianças e adultos) que irão ao evento:")

        participantes = []

        if responsavel.strip():

            participantes.append({
                "nome": responsavel.strip(),
                "faixa": faixa_responsavel
            })

        quantidade = st.selectbox(
            "Quantidade de participantes",
            list(range(0, 11))
        )

        for i in range(quantidade):

            st.markdown(f"### Acompanhante {i+1}")

            col1, col2 = st.columns([3,2])

            with col1:
                nome = st.text_input(
                    "Nome",
                    key=f"nome_{i}"
                )

            with col2:
                faixa = st.selectbox(
                    "Faixa etária",
                    [
                        "Menor de 5 anos",
                        "Entre 5 e 12 anos",
                        "Maior de 12 anos"
                    ],
                    key=f"faixa_{i}"
                )

            if nome.strip():

                participantes.append({
                    "nome": nome.strip(),
                    "faixa": faixa
                })

        if st.button(
            "💖 Confirmar Presença",
            type="primary",
            use_container_width=True
        ):

            if not responsavel:
                st.error("Informe o responsável.")

            elif not responsavel.strip():
                st.error(
                    "Informe o nome do responsável."
                )

            else:

                salvar_confirmacao(
                    responsavel,
                    presenca,
                    participantes
                )

                st.success(
                    "Sua confirmação foi registrada com sucesso! 🎉"
                )
                st.balloons()

                st.markdown("""
                ## 💖 Obrigado pela confirmação!

                Estamos ansiosas para comemorar com você!
                🎂🎈🎉
                """)

# ==========================================
# ADMIN
# ==========================================

if pagina == "Administração":

    st.title("🔒 Administração")

    if "admin_logado" not in st.session_state:
        st.session_state.admin_logado = False

    if not st.session_state.admin_logado:

        usuario = st.text_input("Usuário")

        senha = st.text_input(
            "Senha",
            type="password"
        )

        if st.button("Entrar"):

            if (
                usuario == ADMIN_USUARIO
                and senha == ADMIN_SENHA
            ):

                st.session_state.admin_logado = True
                st.rerun()

            else:
                st.error("Usuário ou senha inválidos.")

    else:

        st.success("Administrador autenticado")

        if st.button("Sair"):
            st.session_state.admin_logado = False
            st.rerun()

        df = carregar_dashboard()

        participantes_df = carregar_participantes()

        menor_5 = len(
            participantes_df[
                participantes_df["faixa"] == "Menor de 5 anos"
            ]
        )

        entre_5_12 = len(
            participantes_df[
                participantes_df["faixa"] == "Entre 5 e 12 anos"
            ]
        )

        maior_12 = len(
            participantes_df[
                participantes_df["faixa"] == "Maior de 12 anos"
            ]
        )

        total_convidados = len(participantes_df)

        total_confirmacoes = len(df)

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "Confirmações",
            total_confirmacoes
        )

        c2.metric(
            "Menores de 5",
            menor_5
        )

        c3.metric(
            "De 5 a 12",
            entre_5_12
        )

        c4.metric(
            "Maiores de 12",
            maior_12
        )

        c5.metric(
            "Total",
            total_convidados
        )

        st.divider()

        st.subheader("🎉 Resumo para Buffet")

        st.success(
            f"""
🎈 Total Convidados: {total_convidados}

👶 Menores de 5 anos: {menor_5}

🧒 De 5 a 12 anos: {entre_5_12}

🧑 Maiores de 12 anos: {maior_12}

✅ Confirmações: {total_confirmacoes}
"""
        )

        st.divider()

        grafico_df = pd.DataFrame({
            "Faixa": [
                "Menores de 5",
                "De 5 a 12",
                "Maiores de 12"
            ],
            "Quantidade": [
                menor_5,
                entre_5_12,
                maior_12
            ]
        })

        fig = px.pie(
            grafico_df,
            names="Faixa",
            values="Quantidade",
            title="Distribuição dos Convidados"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.divider()

        st.subheader("📋 Lista de Participantes")

        st.dataframe(
            participantes_df[
                [
                    "responsavel",
                    "nome",
                    "faixa",
                    "presenca",
                    "data"
                ]
            ],
            use_container_width=True
        )

        st.divider()

        st.subheader("✅ Confirmações Recebidas")

        st.dataframe(
            df,
            use_container_width=True
        )

        st.divider()

        busca = st.text_input(
            "🔍 Buscar participante"
        )

        if busca:

            filtro = participantes_df[
                participantes_df["nome"]
                .str.contains(
                    busca,
                    case=False,
                    na=False
                )
            ]

            st.dataframe(
                filtro,
                use_container_width=True
            )

        st.divider()

        st.subheader("📥 Backup")

        output = io.BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            participantes_df.to_excel(
                writer,
                sheet_name="Participantes",
                index=False
            )

            df.to_excel(
                writer,
                sheet_name="Confirmacoes",
                index=False
            )

        st.download_button(
            "📊 Baixar Excel",
            output.getvalue(),
            "backup_evento.xlsx"
        )