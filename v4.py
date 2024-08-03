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

# Construir o dicionário JSON
credentials_json = {
    "type": st.secrets["type"],
    "project_id": st.secrets["project_id"],
    "private_key_id": st.secrets["private_key_id"],
    "private_key": st.secrets["private_key"],
    "client_email": st.secrets["client_email"],
    "client_id": st.secrets["client_id"],
    "auth_uri": st.secrets["auth_uri"],
    "token_uri": st.secrets["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["client_x509_cert_url"],
    "universe_domain": st.secrets["universe_domain"],
}

credentials_dump = json.dumps(credentials_json)


# --- LEITURA DO ARQUIVO EXCEL ---
@st.cache_data(show_spinner=False)  # Use st.cache_resource em vez de st.cache_data
def load_data(
    sheet_name="CardFinancialModel",
    url_planilha="https://docs.google.com/spreadsheets/d/1Xf4SI-DvRCEvjNalg-T4C4Xcr2G5llrjkb8vsD7cVZA/edit?usp=sharing"
    ):
    
    credentials = pygsheets.authorize(service_account_json=credentials_dump)


    file = credentials.open_by_url(url_planilha)
    tab = file.worksheet_by_title(sheet_name)

    df_all = tab.get_as_df()
    new_row = pd.DataFrame([[""] * len(df_all.columns)], columns=df_all.columns)
    df_all = pd.concat([new_row, df_all]).reset_index(drop=True)

    df_all.replace('(^\s+|\s+$)', '', regex=True, inplace=True)
    
    # print(df_all)
    return df_all
    

df = load_data("CardFinancialModel")
df_cripto = load_data("CriptoFinancialModelYear")
df_3 = load_data("FXFinancialModelYear")
df_4 = load_data("Conta")

ticker = yf.Ticker("BRL=X")
todays_data = ticker.history(period='1d')
dollar = todays_data['Close'].iloc[0]
st.write("Dollar", dollar)

def load_initial_select_values(tab_name, cell_ranges):
    try:
        credentials = pygsheets.authorize(service_account_json=credentials_dump)
        url_planilha = "https://docs.google.com/spreadsheets/d/1Xf4SI-DvRCEvjNalg-T4C4Xcr2G5llrjkb8vsD7cVZA/edit?usp=sharing"
        file = credentials.open_by_url(url_planilha)
        tab = file.worksheet_by_title(tab_name)

        initial_values = []
        for cell_range in cell_ranges:
            initial_values.append(tab.get_value(cell_range))
        return initial_values
    except pygsheets.exceptions.WorksheetNotFound:
        st.error(f"Planilha '{tab_name}' não encontrada.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar valores iniciais: {e}")
        return None

def criar_tabela_aba(df, nome, intervalo, cabecalho=None, remove_blank=False, remove_blank_v2=False):
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
            print("executado no ", nome)
            tabela_df = tabela_df.replace(np.nan, '', regex=True)

        if remove_blank_v2:
            tabela_df = tabela_df.dropna(how='all')

        # Define o cabeçalho se fornecido
        if cabecalho:
            tabela_df.columns = cabecalho

        colunas_multiplicar = tabela_df.columns[2:]
        
        for col in colunas_multiplicar:
            tabela_df[col] = tabela_df[col].astype(str).str.replace('-', '0')        

        for col in colunas_multiplicar:
            tabela_df[col] = tabela_df.apply(
                lambda row: (
                    # 1 IF: If the value is a percentage and the number is integer or float
                    f"{row[col] * 100:.2f}%"
                    if row["Unit"] == "%" and isinstance(row[col], (int, float))

                    # 2 IF: If the unit is "R$" and the number is integer or float, convert to USD 
                    else f"{row[col] / dollar:,.2f}"
                    if row["Unit"] == "R$" and isinstance(row[col], (int, float))

                    # 2 IF: If the unit is "R$" and the number is integer or float, convert to USD 
                    else f"{float(row[col].replace(',','')) / dollar:,.2f}"
                    if row["Unit"] == "R$" and isinstance(row[col], (str)) and not (row[col].startswith("(") and row[col].endswith(")"))

                    # 3 IF: If the unit is "R$" but a string that starts and end with "(", convert to USD and remove parentheses
                    else f"({float(row[col][1:-1].replace(',', '')) / dollar:,.2f})" 
                    if row["Unit"] == "R$" and isinstance(row[col], str) and row[col].startswith("(") and row[col].endswith(")")
                    
                    #  # 4 IF: If the value is a number, keep to two decimal places
                    # else f"{float(row[col].replace(',', '')):,.2f}"
                    # if isinstance(row[col], str) and not ('n/a' in row[col] or '%' in row[col] or (row[col].startswith("(") and row[col].endswith(")")))

                    # 4 IF: If the value is a number, keep to two decimal places
                    else f"{row[col]:,.2f}"
                    if isinstance(row[col], (int, float))

                    # ELSE: If none of the conditions above is true, leave the value unchanged
                    else row[col]
                ),
                axis=1,
            )


        # Exibe a tabela
        def highlight_negatives(val):
            color = "lightcoral" if str(val).startswith("(") else ""
            return f"color: {color}"
        tabela_df['Unit'] = tabela_df['Unit'].apply(lambda x: 'USD' if x == 'R$' else x)

        # tabela_formatada = tabela_df.style.applymap(highlight_negatives, subset=colunas_multiplicar)
        tabela_formatada = tabela_df.style.map(highlight_negatives, subset=colunas_multiplicar)  # Substituição do applymap por map
        

        st.dataframe(tabela_formatada, use_container_width=True)

# --- LAYOUT DA PÁGINA ---
st.title("VOID.TECH")

# --- ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["Card_Processor", "Processor_Cripto-Card", "FX_Card_Processor", "Account"])

with tab1:  # Conteúdo da aba CardFinancialModel  
    st.title("Credit Card")    
    cabecalhoUsers = ["Void: Anual Projections", "Unit"] + [f"Year {i}" for i in range(1, 6)]

    # Criação das tabelas com parâmetros já somados
    criar_tabela_aba(df, "Total # of Active Cardholders", [20, 23, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "Total # of Transactions", [25, 28, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "Total Volume", [30, 33, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(+) Interchange Fee", [35, 38, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Unique Costs", [40, 46, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Processing + BIN Sponsorship", [48, 49, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Active Card", [56, 57, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Minimum Franchise", [64, 65, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Others", [67, 71, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "Total Costs:", [73, 74, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(=) Result - pre flag", [76, 77, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Flag Costs", [79, 88, 2, 8], cabecalho=cabecalhoUsers, remove_blank_v2=True)
    criar_tabela_aba(df, "(=) Result - post flag costs", [110, 111, 2, 8], cabecalho=cabecalhoUsers)

    st.title("Cashback")
    criar_tabela_aba(df, "(=) Premium / Cashback Result", [114, 115, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(+) Month Fee - Premium Clients", [116, 117, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Cashback - Bipa Plus", [118, 119, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(-) Cashback - Bipa 'Normal'", [120, 121, 2, 8], cabecalho=cabecalhoUsers)
    criar_tabela_aba(df, "(=) Consolidated Unit Economics", [123, 124, 2, 8], cabecalho=cabecalhoUsers)

with tab2:  # Conteúdo da aba CriptoFinancialModel (vazia por enquanto)
    st.title("Crypto")
    cabecalhoUsers=["Users", "Unit"] + [f"Year {i}" for i in range(1, 8)]
    criar_tabela_aba(df_cripto, "Users", [12, 14, 2, 10], cabecalho=cabecalhoUsers)

    cabecalhoCriptoT=["Cripto Transactions", "Unit"] + [f"Year {i}" for i in range(1, 8)]
    criar_tabela_aba(df_cripto, "Cripto Transactions", [17, 17, 2, 10], cabecalho=cabecalhoCriptoT)

    cabecalhoCriptoF=["% Cripto Fee", "Unit"] + [f"Year {i}" for i in range(1, 8)]
    criar_tabela_aba(df_cripto, "% Cripto Fee", [25, 25, 2, 10], cabecalho=cabecalhoCriptoF)

    cabecalhoTotal=["Total", "Unit"] + [f"Year {i}" for i in range(1, 8)]
    criar_tabela_aba(df_cripto, "Total", [30, 32, 2, 10], cabecalho=cabecalhoTotal)
  
with tab3:
    st.title("FX")

    cabecalhoUsers=["Title", "Unit"] + [f"Year {i}" for i in range(1, 8)]
    criar_tabela_aba(df_3, "FX", [15, 17, 2, 10], cabecalho=cabecalhoUsers, remove_blank=True)
    criar_tabela_aba(df_3, "Total", [39, 40, 2, 10], cabecalho=cabecalhoUsers, remove_blank=True)
with tab4:
    st.title("Account")

    cabecalhoUsers=["Title", "Unit"] + [f"Yeaer {i}" for i in range(1, 8)]
    criar_tabela_aba(df_4, "Users", [10, 21, 2, 10], cabecalho=cabecalhoUsers, remove_blank=True)