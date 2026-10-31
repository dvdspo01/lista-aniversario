import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import io

import os
from dotenv import load_dotenv

# ==========================================
# CONFIGURAÇÕES
# ==========================================

st.set_page_config(
    page_title="RSVP Evento",
    page_icon="🎉",
    layout="wide"
)
st.markdown("""
<style>

.stApp{
    background-color:#FCE4EC;
}

h1{
    color:#C2185B;
}

h2,h3{
    color:#AD1457;
}

[data-testid="stSidebar"]{
    background-color:#F8BBD0;
}

</style>
""", unsafe_allow_html=True)

LIMITE_VAGAS = 300

import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_USUARIO = os.getenv("ADMIN_USER")
ADMIN_SENHA = os.getenv("ADMIN_PASSWORD")



DB = "evento.db"

# ==========================================
# BANCO
# ==========================================

def conectar():
    return sqlite3.connect(DB, check_same_thread=False)

conn = conectar()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS confirmacoes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_confirmacao TEXT,
    responsavel TEXT,
    presenca TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS participantes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    confirmacao_id INTEGER,
    nome TEXT,
    faixa TEXT,
    FOREIGN KEY(confirmacao_id)
    REFERENCES confirmacoes(id)
)
""")

conn.commit()


# ==========================================
# FUNÇÕES
# ==========================================

def salvar_confirmacao(
        responsavel,
        presenca,
        participantes
):

    cursor.execute("""
        INSERT INTO confirmacoes
        (
            data_confirmacao,
            responsavel,
            presenca
        )
        VALUES (?,?,?)
    """,
    (
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        responsavel,
        presenca
    ))

    confirmacao_id = cursor.lastrowid

    for participante in participantes:

        cursor.execute("""
            INSERT INTO participantes
            (
                confirmacao_id,
                nome,
                faixa
            )
            VALUES (?,?,?)
        """,
        (
            confirmacao_id,
            participante["nome"],
            participante["faixa"]
        ))

    conn.commit()


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

    query = """
    SELECT
        c.id,
        c.data_confirmacao,
        c.responsavel,
        c.presenca,
        COUNT(p.id) quantidade
    FROM confirmacoes c
    LEFT JOIN participantes p
    ON p.confirmacao_id=c.id
    GROUP BY c.id
    """

    return pd.read_sql(query, conn)


def carregar_participantes():

    query = """
    SELECT
        c.responsavel,
        p.nome,
        p.faixa,
        c.presenca,
        c.data_confirmacao
    FROM participantes p
    INNER JOIN confirmacoes c
    ON p.confirmacao_id = c.id
    ORDER BY p.nome
    """

    return pd.read_sql(query, conn)

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
                    "data_confirmacao"
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

        with open("evento.db", "rb") as f:

            st.download_button(
                "🗄️ Baixar Banco SQLite",
                data=f,
                file_name="evento.db"
            )