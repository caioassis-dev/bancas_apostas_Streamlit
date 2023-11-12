
import streamlit as st
from streamlit_folium import folium_static
import folium
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta


caminho_arquivo = "./bancasApostas_saoPaulo.xlsx"
bancasApostas = pd.read_excel(caminho_arquivo)
df_bancasApostas = pd.DataFrame(bancasApostas)

st.set_page_config(layout="wide")
st.title("Bancas de apostas da cidade de São Paulo")

# Função para criar o mapa Folium com marcadores
def create_folium_map():
    m = folium.Map(location=[-23.5489, -46.638823], zoom_start=12)
    return m

locations = {}
for nome_dono, grupo in df_bancasApostas.groupby('NOME DONO DA BANCA'):
    location_info = []
    for index, row in grupo.iterrows():
        location = {
            "LATITUDE/LONGITUDE": [float(coord) for coord in row['LATITUDE/LONGITUDE'].split(', ')],
            "ENDERECO": row['ENDERECO']
        }
        location_info.append(location)
    locations[nome_dono] = location_info

# Exibir o mapa inicial
map = create_folium_map()

# Seletor para escolher nome
selected_location = st.sidebar.multiselect("Escolha os nomes dos donos de bancas:", list(locations.keys()), placeholder="Selecione um ou mais donos")

st.write(f"Localização das bancas do bicheiro:  {', '.join(selected_location)}")

# Atualizar o mapa quando o usuário selecionar nomes
if selected_location:
    map = create_folium_map()
    for name in selected_location:
        for location in locations[name]:
            coords = location["LATITUDE/LONGITUDE"]
            address = location["ENDERECO"]
            folium.Marker(location=coords, popup=address).add_to(map)
    folium_static(map)

# Gráfico consolidado para todas as bancas selecionadas
if selected_location:
    consolidated_df = pd.concat([df_bancasApostas[df_bancasApostas['NOME DONO DA BANCA'] == name] for name in selected_location])

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)
    
    # Aqui estou optando para padronizar a cor dependendo do numero de donos escolhido
    color_column = 'NOME DONO DA BANCA' if len(selected_location) > 1 else 'NOME BANCA'


    bancas_Ativas = px.pie(consolidated_df, values='QUANTIDADE APOSTAS DIA', names='NOME BANCA',
                            title=f"Porcentagem de apostas por dia em cada banca ({', '.join(selected_location)})", color=color_column,
                            color_discrete_sequence=px.colors.qualitative.Set1)
    col1.plotly_chart(bancas_Ativas, use_container_width=True)

    user_input = 0
    numeroDiasCalculo = st.sidebar.text_input("Digite número de dias para simular:")
    if numeroDiasCalculo:
        try:
            user_input = int(numeroDiasCalculo)
        except ValueError:
            st.error("Por favor, insira um valor numérico válido")

    lucroApostasDiaria = pd.DataFrame()
    consolidated_df['RESULTADO VALOR APOSTAS'] = consolidated_df['QUANTIDADE APOSTAS DIA'] * consolidated_df[
        'VALOR DE CADA APOSTA'] * user_input
    lucroApostasDiaria = consolidated_df[['NOME DONO DA BANCA', 'NOME BANCA', 'RESULTADO VALOR APOSTAS']]
    lucro_apostas = px.bar(lucroApostasDiaria, y='RESULTADO VALOR APOSTAS', x='NOME BANCA',
                            title=f"Lucro de apostas referente a simulação de {numeroDiasCalculo} dias ({', '.join(selected_location)})",
                            color=color_column,
                            color_discrete_sequence=px.colors.qualitative.Set1)
    col2.plotly_chart(lucro_apostas, use_container_width=True)

    consolidated_df['PATRIMONIO'] = consolidated_df['PATRIMONIO'].str.replace('[^0-9]', '', regex=True).astype(float)
    consolidated_df['DIVIDA ATIVA'] = consolidated_df['DIVIDA ATIVA'].str.replace('[^0-9]', '', regex=True).astype(float)
    consolidated_df['LUCRO BRUTO'] = consolidated_df['PATRIMONIO'] - consolidated_df['DIVIDA ATIVA']
    consolidated_df['COR'] = np.where(consolidated_df['LUCRO BRUTO'] >= 0, 'Positivo', 'Negativo')

    # Filtrar os dados para criar dois pontos: um positivo e outro negativo
    ponto_positivo = consolidated_df[consolidated_df['COR'] == 'Positivo']
    ponto_negativo = consolidated_df[consolidated_df['COR'] == 'Negativo']
    ponto_positivo['TAMANHO_PONTO'] = 8
    ponto_negativo['TAMANHO_PONTO'] = 8

    # Criar um gráfico de ponto com apenas dois pontos
    scatter_plot = px.scatter(ponto_positivo, x='NOME BANCA', y='LUCRO BRUTO', color_discrete_sequence=['green'],
                              size='TAMANHO_PONTO',title=f"Lucro bruto negativo e positivo")
    scatter_plot.add_trace(px.scatter(ponto_negativo, x='NOME BANCA', y='LUCRO BRUTO', color_discrete_sequence=['red'],
                                     size='TAMANHO_PONTO').data[0])
    col3.plotly_chart(scatter_plot, use_container_width=True)
    
    
    
    data_atual = datetime.now()
    df_contagem_regressiva = pd.DataFrame()
    
    consolidated_df['DIAS RESTANTES PARA RENOVACAO'] = (data_atual - consolidated_df['DATA RENOVACAO LICENCA'])

    df_contagem_regressiva = consolidated_df[['DIAS RESTANTES PARA RENOVACAO','NOME BANCA','NOME DONO DA BANCA','DATA RENOVACAO LICENCA']]
    df_contagem_regressiva['DIAS RESTANTES PARA RENOVACAO'] = pd.to_timedelta(df_contagem_regressiva['DIAS RESTANTES PARA RENOVACAO'])
    df_contagem_regressiva['DIAS RESTANTES PARA RENOVACAO'] = df_contagem_regressiva['DIAS RESTANTES PARA RENOVACAO'].dt.days
    
    diasRestantesRenovacao = px.bar(df_contagem_regressiva, x='DIAS RESTANTES PARA RENOVACAO', y='NOME BANCA',
                            title=f"Dias restantes para renovação de licença:({', '.join(selected_location)})",
                            color=color_column,
                            color_discrete_sequence=px.colors.qualitative.Set1)
    col4.plotly_chart(diasRestantesRenovacao, use_container_width=True)
    