import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# Configuração da página do painel
st.set_page_config(
    page_title="Painel de Corridas VaiGo!",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Painel de Campo & Consultor GPS — VaiGo!")

# Inicializa o banco e insere dados de exemplo se estiver vazio
def inicializar_e_popular_banco():
    conn = sqlite3.connect('corridas_vaigo.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS corridas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            dia_semana TEXT,
            hora TEXT,
            origem TEXT,
            destino TEXT,
            distancia_km REAL,
            ganho_liquido REAL,
            valor_por_km REAL
        )
    ''')
    conn.commit()
    conn.close()

inicializar_e_popular_banco()

# Carrega os dados reais do banco
def carregar_dados():
    conn = sqlite3.connect('corridas_vaigo.db')
    df = pd.read_sql("SELECT * FROM corridas", conn)
    conn.close()
    return df

df = carregar_dados()

if df.empty:
    st.warning("⚠️️ A base de dados está vazia. Execute o leitor de prints primeiro.")
else:
    # Função inteligente e robusta para isolar o bairro corretamente
    def extrair_bairro(row):
        texto = row['origem']
        corrida_id = row['id']
        
        if corrida_id == 19:
            return 'Centro'
        
        if not isinstance(texto, str) or not texto.strip():
            return 'Centro'
        
        texto_lower = texto.lower()
        if 'sergipe' in texto_lower:
            return 'Alvorada'
        if 'octaviano teixeira' in texto_lower:
            return 'Centro'

        if '-' in texto:
            partes = texto.split('-')
            bairro_raw = partes[-1].strip()
            
            if not bairro_raw or bairro_raw.lower() in ['francisco beltrão', 'francisco beltrao', 'pn']:
                return 'Centro'
            
            bairro = bairro_raw.split(',')[0].strip()
            if not bairro or bairro.lower() in ['francisco beltrão', 'francisco beltrao']:
                return 'Centro'
            return bairro
            
        return 'Centro'

    df['Bairro_Origem'] = df.apply(extrair_bairro, axis=1)

    # --- BLOCO 3: PAINEL DE CAMPO COM GPS ATIVO ---
    st.markdown("---")
    st.subheader("🛰️ Bloco 3: Painel de Campo em Tempo Real (GPS Ativo)")

    # Captura automática de data e hora do sistema
    dias_pt = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dia_atual_calc = dias_pt[datetime.now().weekday()]
    hora_atual_calc = datetime.now().strftime("%H:%M")

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"📅 **Dia Atual:** {dia_atual_calc}")
    with col_info2:
        st.info(f"⏰ **Horário Atual:** {hora_atual_calc}")

    # Componente com botão HTML interativo para forçar a permissão do GPS no navegador móvel
    st.markdown("#### 📍 Sua Localização via GPS do Smartphone:")
    
    gps_interactive_code = """
    <div style="font-family:sans-serif; padding: 12px; background-color: #f0f2f6; border-radius: 8px; border-left: 5px solid #ff4b4b;">
        <p style="margin: 0 0 8px 0; font-weight: bold; color: #31333F;">Toque no botão abaixo para capturar o sinal de GPS do seu telemóvel:</p>
        <button onclick="getLocation()" style="background-color: #ff4b4b; color: white; border: none; padding: 10px 16px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 14px;">📍 Obter Localização GPS Atual</button>
        <p id="gps-status" style="margin: 8px 0 0 0; font-size: 13px; color: #555;">Estado: Aguardando clique...</p>
    </div>
    <script>
    function getLocation() {
        document.getElementById("gps-status").innerHTML = "Estado: A solicitar permissão de GPS ao navegador...";
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    let lat = position.coords.latitude;
                    let lon = position.coords.longitude;
                    document.getElementById("gps-status").innerHTML = "✅ GPS Conectado! Lat: " + lat.toFixed(4) + " | Lon: " + lon.toFixed(4);
                },
                function(error) {
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            document.getElementById("gps-status").innerHTML = "⚠️ Permissão negada. Vá às definições do Chrome e permita o acesso à localização para este site.";
                            break;
                        case error.POSITION_UNAVAILABLE:
                            document.getElementById("gps-status").innerHTML = "⚠️️ Informação de localização indisponível.";
                            break;
                        case error.TIMEOUT:
                            document.getElementById("gps-status").innerHTML = "⚠️ Tempo esgotado ao procurar GPS.";
                            break;
                        case error.UNKNOWN_ERROR:
                            document.getElementById("gps-status").innerHTML = "⚠️ Erro desconhecido ao ler GPS.";
                            break;
                    }
                },
                {enableHighAccuracy: true, timeout: 10000, maximumAge: 0}
            );
        } else {
            document.getElementById("gps-status").innerHTML = "❌ O seu navegador não suporta geolocalização.";
        }
    }
    </script>
    """
    components.html(gps_interactive_code, height=130)

    # Seletor de Bairro (com o Miniguaçu já em destaque para teste prático)
    bairros_disponiveis = sorted(df['Bairro_Origem'].unique())
    default_idx = bairros_disponiveis.index('Miniguaçu') if 'Miniguaçu' in bairros_disponiveis else 0
    
    bairro_atual = st.selectbox(
        "Bairro Atual (Confirmar ou Ajustar):", 
        bairros_disponiveis, 
        index=default_idx
    )

    # Execução automática da IA Consultora com o bairro selecionado
    df_local = df[df['Bairro_Origem'] == bairro_atual]
    
    st.markdown(f"### 🎯 Plano Tático Instantâneo para saídas de **{bairro_atual}**")
    
    if df_local.empty:
        st.warning(f"Ainda sem histórico suficiente para **{bairro_atual}**. Desloque-se em direção ao **Centro** para maximizar chamadas.")
    else:
        melhor_destino = df_local['destino'].mode()[0] if not df_local['destino'].empty else "Centro"
        ganho_medio_local = df_local['ganho_liquido'].mean()
        km_medio_local = df_local['valor_por_km'].mean()
        
        st.success(f"""
        **💡 Recomendação do Algoritmo para este momento:**
        * **Destino de Maior Demanda Histórica:** Rota sugerida para **{melhor_destino}**.
        * **Expectativa de Faturamento:** R$ {ganho_medio_local:.2f} por corrida (Média de R$ {km_medio_local:.2f}/km).
        """)

        st.markdown("#### 🗺️ Ações Recomendadas na Pista:")
        if bairro_atual.lower() == 'centro':
            st.markdown("- Mantenha-se nos principais eixos comerciais do Centro para garantir emendas rápidas de corridas.")
        else:
            st.markdown(f"- Fique atento a chamadas que tragam você do **{bairro_atual}** em direção ao **{melhor_destino}**, evitando rodar vazio.")

    st.markdown("---")

    # Resumo Geral da Frota e Histórico
    st.subheader("📊 Visão Geral da Frota")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Corridas", len(df))
    with col2:
        ganho_total = df['ganho_liquido'].sum()
        st.metric("Ganho Líquido Total", f"R$ {ganho_total:.2f}")
    with col3:
        km_total = df['distancia_km'].sum()
        st.metric("Distância Total", f"{km_total:.2f} km")

    st.divider()

    # Relatório de Lucratividade por Bairro
    data_resumo = df.groupby('Bairro_Origem').agg(
        Total_Corridas=('id', 'count'),
        Ganho_Total_R=('ganho_liquido', 'sum'),
        Media_Ganho_R=('ganho_liquido', 'mean'),
        Media_Por_Km=('valor_por_km', 'mean')
    ).reset_index()

    data_resumo['Ganho_Total_R'] = data_resumo['Ganho_Total_R'].round(2)
    data_resumo['Media_Ganho_R'] = data_resumo['Media_Ganho_R'].round(2)
    data_resumo['Media_Por_Km'] = data_resumo['Media_Por_Km'].round(2)
    data_resumo = data_resumo.sort_values(by='Ganho_Total_R', ascending=False).reset_index(drop=True)

    st.subheader("📋 Resumo de Lucratividade por Bairro")
    st.dataframe(data_resumo, use_container_width=True)

    st.divider()

    st.subheader("🗂️ Histórico Completo de Corridas Salvas")
    st.dataframe(df, use_container_width=True)