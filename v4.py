import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pygsheets
import toml
import json
import os


# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="VOID.TECH",
    page_icon="💳",
    layout="wide"
)

# Acessar o segredo TOML
google_sheets_creds = st.secrets["google_sheets"]

# Construir o dicionário JSON
credentials_json = {
    "type": google_sheets_creds["type"],
    "project_id": google_sheets_creds["project_id"],
    "private_key_id": google_sheets_creds["private_key_id"],
    "private_key": google_sheets_creds["private_key"],
    "client_email": google_sheets_creds["client_email"],
    "client_id": google_sheets_creds["client_id"],
    "auth_uri": google_sheets_creds["auth_uri"],
    "token_uri": google_sheets_creds["token_uri"],
    "auth_provider_x509_cert_url": google_sheets_creds["auth_provider_x509_cert_url"],
    "client_x509_cert_url": google_sheets_creds["client_x509_cert_url"],
    "universe_domain": google_sheets_creds["universe_domain"],
}

aa = json.dumps(credentials_json)


# --- LEITURA DO ARQUIVO EXCEL ---
@st.cache_resource(show_spinner=False)  # Use st.cache_resource em vez de st.cache_data
def load_data(
    sheet_name="CardFinancialModel",
    url_planilha="https://docs.google.com/spreadsheets/d/1ANZZQpT6LIWyKHFvzdqcOXEnV99DR3RpPijUE74HXDs/edit?usp=sharing"
    ):
    print(google_sheets_creds)
    print("print(google_sheets_creds)")
    credentials = pygsheets.authorize(service_account_json=aa)



    file = credentials.open_by_url(url_planilha)
    tab = file.worksheet_by_title(sheet_name)

    df_all = tab.get_as_df()
    new_row = pd.DataFrame([[""] * len(df_all.columns)], columns=df_all.columns)
    df_all = pd.concat([new_row, df_all]).reset_index(drop=True)

    df_all.replace('(^\s+|\s+$)', '', regex=True, inplace=True)
    
    # print(df_all)
    return df_all
    

df = load_data("CardFinancialModel")

ticker = yf.Ticker("BRL=X")
todays_data = ticker.history(period='1d')
dollar = todays_data['Close'].iloc[0]

def criar_tabela_aba(df, nome, intervalo, cabecalho=None, remove_blank=False):
    """
    Cria uma tabela Streamlit para dados de criptomoedas, com um expander.

    Args:
        df: DataFrame contendo os dados.
        nome: Título do expander da tabela.
        intervalo: Lista [linha_inicial, linha_final, coluna_inicial, coluna_final].
        cabecalho: Lista com os nomes das colunas (opcional).
    """
    with st.expander(nome, expanded=True):
        # Ajuste no intervalo para incluir a última linha e coluna
        tabela_df = df.iloc[intervalo[0] - 1 : intervalo[1], intervalo[2] - 1 : intervalo[3]]
        
        if remove_blank:
            tabela_df = tabela_df.replace(np.nan, '', regex=True)

        # Define o cabeçalho se fornecido
        if cabecalho:
            tabela_df.columns = cabecalho

        colunas_multiplicar = tabela_df.columns[2:]

        for col in colunas_multiplicar:
            tabela_df[col] = tabela_df.apply(
                lambda row: (
                    f"{row[col] * 100:.2f}%"
                    if row["Unit"] == "%" and isinstance(row[col], (int, float))
                    else f"{row[col] / dollar:,.2f} USD"
                    if row["Unit"] == "R$" and isinstance(row[col], (int, float))
                    else f"({float(row[col][1:-1].replace(',', '')) / dollar:,.2f} USD)"  # Handle parentheses
                    if row["Unit"] == "R$" and isinstance(row[col], str) and row[col].startswith("(") and row[col].endswith(")")
                    else f"{row[col]:,.2f}"
                    if isinstance(row[col], (int, float))
                    else row[col]
                ),
                axis=1,
            )
            

        # Exibe a tabela
        def highlight_negatives(val):
            color = "lightcoral" if str(val).startswith("-") else ""
            return f"color: {color}"
        tabela_df['Unit'] = tabela_df['Unit'].apply(lambda x: 'USD' if x == 'R$' else x)

        # tabela_formatada = tabela_df.style.applymap(highlight_negatives, subset=colunas_multiplicar)
        tabela_formatada = tabela_df.style.map(highlight_negatives, subset=colunas_multiplicar)  # Substituição do applymap por map
        

        st.dataframe(tabela_formatada, use_container_width=True)

# --- LAYOUT DA PÁGINA ---
st.title("VOID.TECH")

# --- ABAS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["CardFinancialModel", "CriptoFinancialModel", "Account", "Original Projection", "Proposed Account", "Proposed Projection"])

def load_tab1(df, dollar):
    cabecalhoUsers = ["Void: Anual Projections", "Unit"] + [f"Year {i}" for i in range(1, 6)]
    criar_tabela_aba(df, "Total # of Active Cardholders", [14, 17, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "Total # of Transactions", [19, 22, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "Total Volume", [24, 27, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(+) Interchange Fee", [29, 32, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Unique Costs", [34, 40, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Processing + BIN Sponsorship", [42, 43, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Active Card", [50, 51, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Minimum Franchise", [58, 59, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Others", [61, 65, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "Total Costs:", [67, 68, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(=) Result - pre flag", [70, 71, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Flag Costs", [73, 82, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(=) Result - post flag costs", [104, 105, 2, 8], cabecalho=cabecalhoUsers)

    st.title("Cashback")
    criar_tabela_aba(df, "(=) Premium / Cashback Result", [108, 109, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(+) Month Fee - Premium Clients", [110, 111, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Cashback - Bipa Plus", [112, 113, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Cashback - Bipa 'Normal'", [114, 115, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(=) Consolidated Unit Economics", [117, 118, 2, 8], cabecalho=cabecalhoUsers)

with tab1:  # Conteúdo da aba CardFinancialModel  
    # cenario_usuarios = st.selectbox("Select Scenario", ["Base", "Upside", "Downside"], index=0)
    # cenario_map = {"Base": 1, "Upside": 2, "Downside": 3}

    # if st.button("Atualizar"):  # Botão que aciona a criação das tabelas
    #     st.write("Você clicou no botão!")

    # --- Dicionário para mapear as opções dos selects para valores numéricos ---
    st.title("Credit Card")

    #  # --- SELECTS ---
    col1, col2, col3 = st.columns(3)  # Cria 3 colunas de largura igual
    with col1:
        cenario_usuarios = st.selectbox("Users", ["Base", "Upside", "Downside"], index=0)
    with col2:
        cenario_transacoes = st.selectbox("Transactions", ["Base", "Upside", "Downside"], index=0)
    with col3:
        cenario_valor_transacao = st.selectbox("Transaction", ["Base", "Upside", "Downside"], index=0)

        # Armazena os valores selecionados no st.session_state
    if "cenario_usuarios_anterior" not in st.session_state:
        st.session_state.cenario_usuarios_anterior = cenario_usuarios
    if "cenario_transacoes_anterior" not in st.session_state:
        st.session_state.cenario_transacoes_anterior = cenario_transacoes
    if "cenario_valor_transacao_anterior" not in st.session_state:
        st.session_state.cenario_valor_transacao_anterior = cenario_valor_transacao

    # Verifica se houve alterações nos valores selecionados
    if (
        cenario_usuarios != st.session_state.cenario_usuarios_anterior
        or cenario_transacoes != st.session_state.cenario_transacoes_anterior
        or cenario_valor_transacao != st.session_state.cenario_valor_transacao_anterior
    ):
        # Atualiza as células no Google Sheets usando pygsheets
        credentials = pygsheets.authorize(service_file=os.getcwd() + "./cred.json")
        url_planilha="https://docs.google.com/spreadsheets/d/1ANZZQpT6LIWyKHFvzdqcOXEnV99DR3RpPijUE74HXDs/edit?usp=sharing"
        file = credentials.open_by_url(url_planilha)
        tab = file.worksheet_by_title("CardFinancialModel")

        if cenario_usuarios != st.session_state.cenario_usuarios_anterior:
            tab.update_value("C5", cenario_usuarios)
            st.session_state.cenario_usuarios_anterior = cenario_usuarios
        if cenario_transacoes != st.session_state.cenario_transacoes_anterior:
            tab.update_value("C7", cenario_transacoes)
            st.session_state.cenario_transacoes_anterior = cenario_transacoes
        if cenario_valor_transacao != st.session_state.cenario_valor_transacao_anterior:
            tab.update_value("C9", cenario_valor_transacao)
            st.session_state.cenario_valor_transacao_anterior = cenario_valor_transacao

        # Limpa o cache e recarrega os dados
        st.cache_resource.clear()
        df = load_data("CardFinancialModel")

    # --- TABELAS ---
    load_tab1(df, dollar)

with tab2:  # Conteúdo da aba CriptoFinancialModel (vazia por enquanto)
    st.title("Crypto")
    df_cripto = load_data("CriptoFinancialModel")

    cabecalhoUsers=["Users", "Unit"] + [f"Month {i}" for i in range(1, 61)]
    criar_tabela_aba(df_cripto, "Users", [11, 13, 2, 63], cabecalho=cabecalhoUsers)

    cabecalhoCriptoT=["Cripto Transactions", "Unit"] + [f"Month {i}" for i in range(1, 61)]
    criar_tabela_aba(df_cripto, "Cripto Transactions", [16, 16, 2, 63], cabecalho=cabecalhoCriptoT)

    cabecalhoCriptoF=["% Cripto Fee", "Unit"] + [f"Month {i}" for i in range(1, 61)]
    criar_tabela_aba(df_cripto, "% Cripto Fee", [24, 24, 2, 63], cabecalho=cabecalhoCriptoF)

    cabecalhoTotal=["Total", "Unit"] + [f"Month {i}" for i in range(1, 61)]
    criar_tabela_aba(df_cripto, "Total", [29, 31, 2, 63], cabecalho=cabecalhoTotal)
  

with tab3:
    st.title("Account")

    df_cripto = load_data("Conta")

    cabecalhoUsers=["Title", "Unit"] + [f"Month {i}" for i in range(1, 61)]
    criar_tabela_aba(df_cripto, "Users", [10, 22, 2, 63], cabecalho=cabecalhoUsers, remove_blank=True)
with tab4:
    st.title("Original Projection")

    df_cripto = load_data("Projecao-Original")

    cabecalhoUsers=["Title", "Unit"] + [f"Year {i}" for i in range(1, 6)]
    criar_tabela_aba(df_cripto, "Users", [5, 19, 2, 8], cabecalho=cabecalhoUsers, remove_blank=True)
with tab5:
    st.title("Proposed Account")

    df_cripto = load_data("Conta-Proposta")

    cabecalhoUsers=["Title", "Unit"] + [f"Month {i}" for i in range(1, 61)]
    criar_tabela_aba(df_cripto, "Users", [10, 22, 2, 63], cabecalho=cabecalhoUsers, remove_blank=True)
with tab6:
    st.title("Proposed Projection")

    df_cripto = load_data("Projecao-Proposta")

    cabecalhoUsers=["Title", "Unit"] + [f"Year {i}" for i in range(1, 6)]
    criar_tabela_aba(df_cripto, "Users", [4, 18, 2, 8], cabecalho=cabecalhoUsers, remove_blank=True)
