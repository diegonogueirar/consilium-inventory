import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
import libsql_experimental as libsql

st.set_page_config(page_title="Consilium | Inventory Control", page_icon="🚢", layout="wide")

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def validar_email_profissional(email):
    dominios_proibidos = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "icloud.com", "live.com", "aol.com"]
    partes = email.split("@")
    if len(partes) != 2:
        return False
    dominio = partes[1].lower()
    if dominio in dominios_proibidos:
        return False
    return True

def aplicar_estilo_consilium():
    bg_image_css = ""
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        bg_image_css = f"""
        .stApp {{
            background-color: #0e1117 !important;
        }}
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.95)), url("data:image/png;base64,{data}");
            background-repeat: no-repeat;
            background-position: center;
            background-size: cover;
            pointer-events: none;
            z-index: 0;
        }}
        """
    else:
        bg_image_css = """
        .stApp::before {
            content: "CONSILIUM";
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-15deg);
            font-size: 16vw;
            font-weight: 900;
            letter-spacing: 20px;
            color: rgba(255, 255, 255, 0.025);
            pointer-events: none;
            z-index: 0;
            white-space: nowrap;
        }
        """

    st.markdown(f"""
        <style>
        {bg_image_css}
        .stApp > div {{ position: relative; z-index: 1; }}
        
        div.stButton > button, div.stFormSubmitButton > button {{
            background: linear-gradient(135deg, #003366 0%, #005b9f 100%);
            color: white !important;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.15);
            padding: 10px 22px;
            font-weight: 700;
            font-size: 15px;
            transition: all 0.25s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}
        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0, 91, 159, 0.6);
            background: linear-gradient(135deg, #004488 0%, #0073c7 100%);
        }}
        button[data-baseweb="tab"] {{
            font-size: 15px !important;
            font-weight: 600 !important;
            padding: 10px 18px !important;
            border-radius: 8px 8px 0 0 !important;
        }}
        
        div[data-testid="stMetric"] {{
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-left: 5px solid #0073c7;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        }}
        div[data-testid="stMetric"] label {{ color: #94a3b8 !important; }}
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{ color: #f8fafc !important; }}

        .header-consilium {{
            background: linear-gradient(90deg, #001122 0%, #002244 60%, #003366 100%);
            padding: 20px 28px;
            border-radius: 14px;
            color: white;
            margin-bottom: 22px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .logo-titulo {{ font-size: 28px; font-weight: 900; letter-spacing: 4px; margin: 0; color: #ffffff; }}
        .logo-subtitulo {{ font-size: 13px; color: #94a3b8; letter-spacing: 1px; margin-top: 4px; }}
        </style>
    """, unsafe_allow_html=True)

aplicar_estilo_consilium()

@st.cache_resource
def iniciar_banco():
    try:
        url = st.secrets["TURSO_DATABASE_URL"]
        token = st.secrets["TURSO_AUTH_TOKEN"]
    except KeyError:
        st.error("Erro: As credenciais do Turso não foram encontradas no Secrets do Streamlit.")
        st.stop()
        
    conn = libsql.connect(url, auth_token=token)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS estoque (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spare_part TEXT NOT NULL,
                    numero_serie TEXT,
                    quantidade INTEGER NOT NULL,
                    localizacao TEXT NOT NULL,
                    part_number TEXT,
                    estoque_origem TEXT DEFAULT 'Santa Catarina',
                    system TEXT DEFAULT 'General'
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS navios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_navio TEXT UNIQUE NOT NULL,
                    sg_number TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS estoque_navios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    navio TEXT NOT NULL,
                    spare_part TEXT NOT NULL,
                    part_number TEXT,
                    numero_serie TEXT,
                    quantidade INTEGER NOT NULL,
                    estoque_origem TEXT NOT NULL,
                    system TEXT NOT NULL
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_hora TEXT NOT NULL,
                    usuario TEXT NOT NULL,
                    tipo_movimento TEXT NOT NULL,
                    spare_part TEXT NOT NULL,
                    numero_serie TEXT,
                    quantidade INTEGER NOT NULL,
                    navio TEXT,
                    work_order TEXT,
                    part_number TEXT,
                    estoque_origem TEXT,
                    system TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    nome_completo TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    senha_hash TEXT NOT NULL,
                    perfil TEXT NOT NULL DEFAULT 'TECNICO',
                    status TEXT NOT NULL DEFAULT 'PENDENTE',
                    data_cadastro TEXT NOT NULL,
                    pedido_reset INTEGER DEFAULT 0,
                    session_token TEXT
                )''')
                
    c.execute('''CREATE TABLE IF NOT EXISTS config_email (
                    id INTEGER PRIMARY KEY,
                    smtp_server TEXT,
                    smtp_port INTEGER,
                    email_remetente TEXT,
                    senha_app TEXT
                )''')
                
    c.execute('''CREATE TABLE IF NOT EXISTS ferramentas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ferramenta TEXT NOT NULL,
                    identificacao TEXT,
                    usuario TEXT NOT NULL,
                    data_retirada TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'EM POSSE',
                    system TEXT DEFAULT 'General',
                    part_number TEXT,
                    quantidade INTEGER DEFAULT 1,
                    observacao TEXT DEFAULT ''
                )''')
    
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("SELECT COUNT(*) FROM usuarios WHERE perfil = 'ADMIN'")
    if c.fetchone()[0] == 0:
        try:
            c.execute("INSERT INTO usuarios (username, nome_completo, email, senha_hash, perfil, status, data_cadastro) VALUES (?, ?, ?, ?, 'ADMIN', 'APROVADO', ?)",
                      ('admin', 'General Administrator', 'admin@consilium.com', hash_senha('1234'), agora))
        except Exception:
            pass
    
    conn.commit()
    return conn

conn = iniciar_banco()

def ler_banco(query, params=()):
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    cols = [desc[0] for desc in c.description] if c.description else []
    return pd.DataFrame(rows, columns=cols)

def limpar_dado(valor):
    if pd.isna(valor) or valor is None:
        return ""
    return str(valor).strip()

def enviar_email_recuperacao(email_destino, nome_usuario, nova_senha):
    c = conn.cursor()
    c.execute("SELECT smtp_server, smtp_port, email_remetente, senha_app FROM config_email WHERE id = 1")
    cfg = c.fetchone()
    if not cfg or not cfg[2] or not cfg[3]:
        return False, "SMTP server not configured."
    try:
        corpo = f"Hello, {nome_usuario}!\n\nYour temporary password is: {nova_senha}\nPlease access the system and change it in My Profile."
        msg = MIMEText(corpo)
        msg['Subject'] = "Consilium - Password Recovery"
        msg['From'] = cfg[2]
        msg['To'] = email_destino
        with smtplib.SMTP(cfg[0], int(cfg[1])) as server:
            server.starttls()
            server.login(cfg[2], cfg[3])
            server.send_message(msg)
        return True, "Email sent!"
    except Exception as e:
        return False, str(e)

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_atual = ""
    st.session_state.nome_atual = ""
    st.session_state.perfil_atual = ""
    
    if "session" in st.query_params:
        token = st.query_params["session"]
        c = conn.cursor()
        c.execute("SELECT username, nome_completo, perfil FROM usuarios WHERE session_token = ? AND status = 'APROVADO'", (token,))
        user_sess = c.fetchone()
        if user_sess:
            st.session_state.logado = True
            st.session_state.usuario_atual = str(user_sess[0])
            st.session_state.nome_atual = str(user_sess[1])
            st.session_state.perfil_atual = str(user_sess[2])

if not st.session_state.logado:
    st.markdown("""
        <div class="header-consilium">
            <div>
                <div class="logo-titulo">CONSILIUM</div>
                <div class="logo-subtitulo">MARINE & SAFETY — SPARE PARTS INVENTORY CONTROL</div>
            </div>
            <div style="font-size: 32px;">🚢</div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        if os.path.exists("logo.png"):
            st.image("logo.png", use_container_width=True)
            
        aba_login, aba_criar, aba_recuperar = st.tabs(["Login", "Sign Up", "Forgot Password"])
        
        with aba_login:
            with st.form("form_login"):
                st.subheader("System Access")
                usuario_input = st.text_input("Username or Professional Email").strip().lower()
                senha_input = st.text_input("Password", type="password")
                entrar = st.form_submit_button("Sign In", use_container_width=True)
                
                if entrar:
                    c = conn.cursor()
                    c.execute("SELECT username, nome_completo, senha_hash, perfil, status FROM usuarios WHERE LOWER(username) = ? OR LOWER(email) = ?", (str(usuario_input), str(usuario_input)))                    user_row = c.fetchone()
                    if not user_row:
                        st.error("User or email not found.")
                    elif user_row[2] != hash_senha(senha_input):
                        st.error("Incorrect password.")
                    elif user_row[4] == "PENDENTE":
                        st.warning("Your account is pending Administrator approval.")
                    elif user_row[4] == "BLOQUEADO":
                        st.error("Account deactivated.")
                    else:
                        token = secrets.token_hex(16)
                        c.execute("UPDATE usuarios SET session_token = ? WHERE username = ?", (token, str(user_row[0])))
                        conn.commit()
                        st.query_params["session"] = token
                        
                        st.session_state.logado = True
                        st.session_state.usuario_atual = str(user_row[0])
                        st.session_state.nome_atual = str(user_row[1])
                        st.session_state.perfil_atual = str(user_row[3])
                        st.rerun()

        with aba_criar:
            with st.form("form_criar_conta", clear_on_submit=True):
                st.subheader("Request New Access")
                st.caption("Only professional corporate emails are allowed.")
                novo_user = st.text_input("Username *", placeholder="ex: john.smith").strip().lower()
                novo_nome = st.text_input("Full Name *", placeholder="ex: John Smith").strip()
                novo_email = st.text_input("Professional Email *", placeholder="ex: john@consilium.com").strip().lower()
                nova_senha1 = st.text_input("Password *", type="password")
                nova_senha2 = st.text_input("Confirm Password *", type="password")
                btn_solicitar = st.form_submit_button("Request Account", use_container_width=True)
                
                if btn_solicitar:
                    if not novo_user or not novo_nome or not novo_email or not nova_senha1:
                        st.error("Please fill in all required fields.")
                    elif " " in novo_user:
                        st.error("Username cannot contain spaces.")
                    elif not validar_email_profissional(novo_email):
                        st.error("Personal emails (Gmail, Outlook, Yahoo, etc.) are not allowed. Please use a professional email.")
                    elif nova_senha1 != nova_senha2:
                        st.error("Passwords do not match.")
                    else:
                        try:
                            c = conn.cursor()
                            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
                            sql_novo = "INSERT INTO usuarios (username, nome_completo, email, senha_hash, perfil, status, data_cadastro) VALUES (?, ?, ?, ?, 'TECNICO', 'PENDENTE', ?)"
                            c.execute(sql_novo, (novo_user, novo_nome, novo_email, hash_senha(nova_senha1), agora))
                            conn.commit()
                            st.success("Request sent successfully! Awaiting Administrator approval.")
                        except Exception:
                            st.error("Username or professional email already registered.")

        with aba_recuperar:
            with st.form("form_recuperar"):
                st.subheader("Recover Password")
                email_rec = st.text_input("Enter your registered professional email *").strip().lower()
                btn_rec = st.form_submit_button("Reset Password", use_container_width=True)
                if btn_rec:
                    c = conn.cursor()
                    c.execute("SELECT id, nome_completo, username FROM usuarios WHERE LOWER(email) = ?", (email_rec,))
                    u_rec = c.fetchone()
                    if not u_rec:
                        st.error("Email not found.")
                    else:
                        senha_temp = secrets.token_hex(3).upper()
                        enviado, _ = enviar_email_recuperacao(email_rec, str(u_rec[1]), senha_temp)
                        if enviado:
                            c.execute("UPDATE usuarios SET senha_hash = ?, pedido_reset = 0 WHERE id = ?", (hash_senha(senha_temp), int(u_rec[0])))
                            conn.commit()
                            st.success("Temporary password sent to your email.")
                        else:
                            c.execute("UPDATE usuarios SET pedido_reset = 1 WHERE id = ?", (int(u_rec[0]),))
                            conn.commit()
                            st.info("Request sent directly to the Administrator panel.")
    st.stop()

col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    badge_perfil = "ADMINISTRATOR" if st.session_state.perfil_atual == "ADMIN" else "TECHNICIAN"
    st.markdown(f"""
        <div class="header-consilium">
            <div>
                <div class="logo-titulo">CONSILIUM</div>
                <div class="logo-subtitulo">INVENTORY MANAGEMENT & WORK ORDERS SYSTEM</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 12px; color: #ffd966; font-weight: bold;">{badge_perfil}</div>
                <div style="font-size: 17px; font-weight: bold;">User: {st.session_state.nome_atual}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.write("")
    if os.path.exists("logo.png"):
        st.image("logo.png", width=110)
    if st.button("Sign Out", use_container_width=True):
        c = conn.cursor()
        c.execute("UPDATE usuarios SET session_token = NULL WHERE username = ?", (str(st.session_state.usuario_atual),))
        conn.commit()
        if "session" in st.query_params:
            del st.query_params["session"]
            
        st.session_state.logado = False
        st.rerun()

if st.session_state.perfil_atual == "ADMIN":
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM usuarios WHERE status = 'PENDENTE' OR pedido_reset = 1")
    pendencias = c.fetchone()[0]
    if pendencias > 0:
        st.warning(f"Attention Administrator: There are {pendencias} pending request(s) in the Admin Panel tab.")

df_est_total = ler_banco("SELECT * FROM estoque")
df_hist_total = ler_banco("SELECT * FROM historico WHERE tipo_movimento = 'OUT (SERVICE)' OR tipo_movimento = 'OUT (VESSEL SERVICE)'")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Registered Models (Main)", len(df_est_total))
k2.metric("Available Parts (Main)", int(df_est_total['quantidade'].sum()) if not df_est_total.empty else 0)
k3.metric("Zeroed Parts (Main)", len(df_est_total[df_est_total['quantidade'] == 0]) if not df_est_total.empty else 0)
k4.metric("Total Service Dispatches", len(df_hist_total))

st.write("")

lista_abas = [
    "Checkout Parts (Main)", 
    "Vessels Inventory", 
    "Check Inventory", 
    "Register Part", 
    "Add/Restock Parts", 
    "Tools (Cautela)", 
    "Service Checkouts", 
    "Full History", 
    "My Profile"
]

if st.session_state.perfil_atual == "ADMIN":
    lista_abas.append("Admin Panel")

abas = st.tabs(lista_abas)

with abas[0]:
    st.subheader("Register Part Usage on Vessel (From Main Inventory)")
    df_disponivel = ler_banco("SELECT * FROM estoque WHERE quantidade > 0")
    if df_disponivel.empty:
        st.info("No parts available in stock at the moment.")
    else:
        opcoes_pecas = {}
        for _, row in df_disponivel.iterrows():
            pn_val = row.get('part_number', '')
            sn_val = row.get('numero_serie', '')
            sys_val = row.get('system', '')
            orig_val = row.get('estoque_origem', '')
            
            pn_text = f" | P/N: {pn_val}" if pn_val else ""
            sn_text = f" | S/N: {sn_val}" if sn_val else ""
            label = f"[{orig_val}] {row['spare_part']}{pn_text}{sn_text} | Sys: {sys_val} (Avail: {row['quantidade']})"
            opcoes_pecas[label] = row['id']
        
        with st.form("form_baixa_servico"):
            peca_selecionada_label = st.selectbox("Select Part", list(opcoes_pecas.keys()))
            col_q, col_n, col_w = st.columns([1, 2, 2])
            with col_q:
                qtd_retirada = st.number_input("Quantity", min_value=1, step=1, value=1)
            with col_n:
                navio = st.text_input("Vessel Name *", placeholder="Ex: MV Atlantic")
            with col_w:
                work_order = st.text_input("Work Order (WO) *", placeholder="Ex: WO-2026-105")
                
            btn_confirmar = st.form_submit_button("Confirm Checkout", use_container_width=True)
            if btn_confirmar:
                id_peca = opcoes_pecas[peca_selecionada_label]
                dados_peca = df_disponivel[df_disponivel['id'] == id_peca].iloc[0]
                if not navio.strip() or not work_order.strip():
                    st.error("Vessel Name and Work Order are required.")
                elif qtd_retirada > dados_peca['quantidade']:
                    st.error("Insufficient stock quantity.")
                else:
                    nova_qtd = int(dados_peca['quantidade'] - qtd_retirada)
                    c = conn.cursor()
                    c.execute("UPDATE estoque SET quantidade = ? WHERE id = ?", (nova_qtd, int(id_peca)))
                    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    sql_hist = "INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    c.execute(sql_hist, (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "OUT (SERVICE)", dados_peca['spare_part'], dados_peca.get('part_number', ''), dados_peca.get('numero_serie', ''), int(qtd_retirada), dados_peca.get('estoque_origem', ''), dados_peca.get('system', ''), navio.strip(), work_order.strip()))
                    conn.commit()
                    st.success(f"Checkout successfully recorded for vessel {navio}!")
                    st.rerun()

with abas[1]:
    st.subheader("Vessel-Specific Inventory")
    st.info("Manage dedicated spare parts assigned exclusively to specific vessels (Independent from Main Warehouse).")
    
    if st.session_state.perfil_atual == "ADMIN":
        with st.expander("➕ Register or Remove Vessel"):
            col_v1, col_v2 = st.columns([1, 1])
            with col_v1:
                with st.form("form_novo_navio", clear_on_submit=True):
                    st.markdown("#### Register New Vessel")
                    novo_navio_nome = st.text_input("Vessel Name *", placeholder="Ex: MV Atlantic")
                    novo_sg_number = st.text_input("SG Number *", placeholder="Ex: SG-12345")
                    
                    btn_novo_navio = st.form_submit_button("Save Vessel", use_container_width=True)
                    if btn_novo_navio:
                        if not novo_navio_nome.strip() or not novo_sg_number.strip():
                            st.error("Vessel Name and SG Number are required.")
                        else:
                            c = conn.cursor()
                            c.execute("SELECT nome_navio, sg_number FROM navios WHERE UPPER(nome_navio) = ? OR UPPER(sg_number) = ?", 
                                      (novo_navio_nome.strip().upper(), novo_sg_number.strip().upper()))
                            duplicata = c.fetchone()
                            
                            if duplicata:
                                st.error(f"⚠️ Error: A vessel is already registered with the Name '{duplicata[0]}' or SG Number '{duplicata[1]}'. Duplicates are not allowed.")
                            else:
                                c.execute("INSERT INTO navios (nome_navio, sg_number) VALUES (?, ?)", (novo_navio_nome.strip().upper(), novo_sg_number.strip().upper()))
                                conn.commit()
                                st.success(f"Vessel '{novo_navio_nome.upper()}' registered successfully!")
                                st.rerun()
            
            with col_v2:
                with st.form("form_remover_navio", clear_on_submit=True):
                    st.markdown("#### Remove Vessel")
                    df_nav_rem = ler_banco("SELECT nome_navio FROM navios ORDER BY nome_navio")
                    lista_nav_rem = df_nav_rem['nome_navio'].tolist() if not df_nav_rem.empty else []
                    
                    v_rem_navio = st.selectbox("Select Vessel to Remove *", lista_nav_rem if lista_nav_rem else ["No vessels registered"])
                    v_rem_motivo = st.text_input("Reason for Removal *", placeholder="Ex: Vessel sold, project ended...")
                    
                    btn_rem_navio = st.form_submit_button("🗑️ Remove Vessel", use_container_width=True)
                    if btn_rem_navio:
                        if not lista_nav_rem:
                            st.error("No vessels available to remove.")
                        elif not v_rem_motivo.strip():
                            st.error("A reason is required to remove a vessel.")
                        else:
                            c = conn.cursor()
                            c.execute("DELETE FROM navios WHERE nome_navio = ?", (str(v_rem_navio),))
                            c.execute("DELETE FROM estoque_navios WHERE navio = ?", (str(v_rem_navio),))
                            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            c.execute("INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                      (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "DELETE (VESSEL)", "ALL ASSOCIATED PARTS REMOVED", "", "", 0, "N/A", "N/A", str(v_rem_navio), f"REMOVED: {v_rem_motivo.strip()}"))
                            conn.commit()
                            st.success(f"Vessel '{v_rem_navio}' and all its specific inventory were successfully removed!")
                            st.rerun()

    st.markdown("---")
    
    df_navios = ler_banco("SELECT nome_navio FROM navios ORDER BY nome_navio")
    lista_navios = df_navios['nome_navio'].tolist() if not df_navios.empty else []
    
    if not lista_navios:
        st.info("No vessels registered yet.")
    else:
        filtro_navio = st.selectbox("🔍 Select a Vessel to view its inventory or add new parts:", ["All Vessels"] + lista_navios)
        
        if filtro_navio != "All Vessels":
            col_v_act1, col_v_act2 = st.columns([1, 1])
            
            with col_v_act1:
                with st.expander(f"🛠️ Register Part Usage on '{filtro_navio}'", expanded=False):
                    st.markdown(f"**Checkout an item currently stored in {filtro_navio} for a service.**")
                    df_v_disp = ler_banco("SELECT * FROM estoque_navios WHERE navio = ? AND quantidade > 0", (str(filtro_navio),))
                    if df_v_disp.empty:
                        st.info("No parts available in this vessel's stock.")
                    else:
                        opcoes_v_disp = {}
                        for _, row in df_v_disp.iterrows():
                            pn_text = f" | P/N: {row['part_number']}" if row['part_number'] else ""
                            sn_text = f" | S/N: {row['numero_serie']}" if row['numero_serie'] else ""
                            label = f"[{row['estoque_origem']}] {row['spare_part']}{pn_text}{sn_text} | Sys: {row['system']} (Avail: {row['quantidade']})"
                            opcoes_v_disp[label] = row['id']
                            
                        with st.form("form_uso_navio"):
                            v_peca_uso_label = st.selectbox("Select Part to Use", list(opcoes_v_disp.keys()))
                            col_vu1, col_vu2 = st.columns(2)
                            with col_vu1:
                                v_qtd_uso = st.number_input("Quantity Used", min_value=1, step=1, value=1)
                            with col_vu2:
                                v_wo_uso = st.text_input("Work Order / SG Number *", placeholder="Ex: WO-1025")
                                
                            btn_uso_navio = st.form_submit_button("Confirm Usage", use_container_width=True)
                            if btn_uso_navio:
                                id_uso = opcoes_v_disp[v_peca_uso_label]
                                row_uso = df_v_disp[df_v_disp['id'] == id_uso].iloc[0]
                                if not v_wo_uso.strip():
                                    st.error("Work Order / SG Number is required.")
                                elif v_qtd_uso > row_uso['quantidade']:
                                    st.error("Insufficient stock!")
                                else:
                                    nova_qtd_u = int(row_uso['quantidade'] - v_qtd_uso)
                                    c = conn.cursor()
                                    c.execute("UPDATE estoque_navios SET quantidade = ? WHERE id = ?", (nova_qtd_u, int(id_uso)))
                                    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                    c.execute("INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                              (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "OUT (VESSEL SERVICE)", row_uso['spare_part'], row_uso.get('part_number', ''), row_uso.get('numero_serie', ''), int(v_qtd_uso), row_uso.get('estoque_origem', ''), row_uso.get('system', ''), str(filtro_navio), v_wo_uso.strip()))
                                    conn.commit()
                                    st.success(f"Usage registered for {filtro_navio}!")
                                    st.rerun()

            with col_v_act2:
                if st.session_state.perfil_atual == "ADMIN":
                    with st.expander(f"📦 Add New Part to '{filtro_navio}' Inventory", expanded=False):
                        with st.form("form_add_peca_navio", clear_on_submit=True):
                            col_p1, col_p2 = st.columns(2)
                            with col_p1:
                                v_spare = st.text_input("Spare Part Name *")
                                v_pn = st.text_input("Part Number (P/N)")
                                v_sys = st.text_input("System *")
                            with col_p2:
                                v_sn = st.text_input("Serial Number (S/N)")
                                v_qtd = st.number_input("Quantity *", min_value=1, step=1, value=1)
                                v_wh = st.selectbox("Warehouse *", ["Santa Catarina", "Duci", "Diego"])
                            
                            btn_v_peca = st.form_submit_button(f"Save Part to {filtro_navio}", use_container_width=True)
                            if btn_v_peca:
                                if not v_spare.strip() or not v_sys.strip():
                                    st.error("Spare Part and System are required.")
                                else:
                                    c = conn.cursor()
                                    val_pn = v_pn.strip() if v_pn else ""
                                    val_sn = v_sn.strip() if v_sn else ""
                                    
                                    c.execute("INSERT INTO estoque_navios (navio, spare_part, part_number, numero_serie, quantidade, estoque_origem, system) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                              (str(filtro_navio), v_spare.strip(), val_pn, val_sn, int(v_qtd), v_wh, v_sys.strip()))
                                    
                                    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                                    c.execute("INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                              (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "IN (VESSEL STOCK)", v_spare.strip(), val_pn, val_sn, int(v_qtd), v_wh, v_sys.strip(), str(filtro_navio), "REGISTER"))
                                    conn.commit()
                                    st.success(f"Part successfully registered directly to {filtro_navio}!")
                                    st.rerun()

        query_v = "SELECT id AS 'ID', navio AS 'Vessel', estoque_origem AS 'Warehouse', spare_part AS 'Spare Part', part_number AS 'Part Number', numero_serie AS 'Serial Number', quantidade AS 'Qty', system AS 'System' FROM estoque_navios"
        params_v = []
        if filtro_navio != "All Vessels":
            query_v += " WHERE navio = ?"
            params_v.append(str(filtro_navio))
            
        df_v_estoque = ler_banco(query_v, tuple(params_v))
        st.caption(f"Showing {len(df_v_estoque)} item(s) for {filtro_navio}.")
        
        if st.session_state.perfil_atual == "ADMIN":
            edited_v_df = st.data_editor(
                df_v_estoque,
                use_container_width=True,
                hide_index=True,
                disabled=["ID", "Vessel"],
                column_config={
                    "Warehouse": st.column_config.SelectboxColumn("Warehouse", options=["Santa Catarina", "Duci", "Diego"], required=True),
                    "Qty": st.column_config.NumberColumn("Qty", min_value=0, step=1, required=True),
                    "Spare Part": st.column_config.TextColumn("Spare Part", required=True),
                    "System": st.column_config.TextColumn("System", required=True)
                }
            )
            
            mudancas_v = []
            for i in range(len(df_v_estoque)):
                r_orig = df_v_estoque.iloc[i]
                r_edit = edited_v_df.iloc[i]
                if not r_orig.equals(r_edit):
                    mudancas_v.append((r_orig, r_edit))
            
            if mudancas_v:
                st.warning(f"⚠️ You have {len(mudancas_v)} unsaved change(s) in the vessel inventory.")
                with st.form("form_save_vessel_edits"):
                    motivo_v_edit = st.text_input("Reason for edits (Required for Log) *", placeholder="Ex: Audit update, S/N corrected...")
                    if st.form_submit_button("💾 Save Vessel Inventory Edits", use_container_width=True):
                        if not motivo_v_edit.strip():
                            st.error("Reason is required.")
                        else:
                            c = conn.cursor()
                            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            for orig, edit in mudancas_v:
                                id_p = int(edit['ID'])
                                val_sp = limpar_dado(edit['Spare Part'])
                                val_pn = limpar_dado(edit['Part Number'])
                                val_sn = limpar_dado(edit['Serial Number'])
                                val_wh = limpar_dado(edit['Warehouse'])
                                val_sys = limpar_dado(edit['System'])
                                val_qtd = int(edit['Qty'])
                                
                                c.execute("UPDATE estoque_navios SET spare_part=?, part_number=?, numero_serie=?, quantidade=?, estoque_origem=?, system=? WHERE id=?",
                                          (val_sp, val_pn, val_sn, val_qtd, val_wh, val_sys, id_p))
                                
                                obs_mov = f"EDIT (VESSEL): {motivo_v_edit.strip()}"
                                c.execute("INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                          (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "EDIT (VESSEL STOCK)", val_sp, val_pn, val_sn, val_qtd, val_wh, val_sys, str(edit['Vessel']), obs_mov))
                            conn.commit()
                            st.success("Vessel inventory updated successfully!")
                            st.rerun()
        else:
            st.dataframe(df_v_estoque, use_container_width=True, hide_index=True)

with abas[2]:
    st.subheader("Main Inventory Lookup & Edit")
    df_estoque = ler_banco("SELECT id AS 'ID', estoque_origem AS 'Warehouse', spare_part AS 'Spare Part', part_number AS 'Part Number', numero_serie AS 'Serial Number', quantidade AS 'Current Qty', system AS 'System' FROM estoque")
    
    busca = st.text_input("Search (Partial characters allowed, e.g., part name, P/N, S/N, warehouse or system)...", value="", placeholder="Type to filter. Clear the text to show all items again.")
    
    if busca.strip():
        busca_lower = busca.strip().lower()
        filtro = (
            df_estoque['Warehouse'].str.lower().str.contains(busca_lower, na=False) |
            df_estoque['Spare Part'].str.lower().str.contains(busca_lower, na=False) |
            df_estoque['Part Number'].str.lower().str.contains(busca_lower, na=False) |
            df_estoque['Serial Number'].str.lower().str.contains(busca_lower, na=False) |
            df_estoque['System'].str.lower().str.contains(busca_lower, na=False)
        )
        df_estoque = df_estoque[filtro]
    
    st.caption(f"Showing {len(df_estoque)} item(s).")
    
    def highlight_zero_stock(row):
        if row['Current Qty'] == 0:
            return ['background-color: rgba(255, 77, 77, 0.25); color: #ffcccc;'] * len(row)
        return [''] * len(row)

    styled_df_estoque = df_estoque.style.apply(highlight_zero_stock, axis=1)
    
    if st.session_state.perfil_atual == "ADMIN":
        st.markdown("💡 **Admin Mode:** Edit values directly in the table below. Click the 'Warehouse' cell to see the dropdown.")
        
        edited_df = st.data_editor(
            styled_df_estoque,
            use_container_width=True,
            hide_index=True,
            disabled=["ID"],
            column_config={
                "Warehouse": st.column_config.SelectboxColumn("Warehouse", options=["Santa Catarina", "Duci", "Diego"], required=True),
                "Current Qty": st.column_config.NumberColumn("Current Qty", min_value=0, step=1, required=True),
                "Spare Part": st.column_config.TextColumn("Spare Part", required=True),
                "System": st.column_config.TextColumn("System", required=True)
            }
        )
        
        mudancas = []
        for i in range(len(df_estoque)):
            row_orig = df_estoque.iloc[i]
            row_edit = edited_df.iloc[i]
            if not row_orig.equals(row_edit):
                mudancas.append((row_orig, row_edit))
        
        if mudancas:
            st.warning(f"⚠️ You have {len(mudancas)} unsaved change(s) in the main inventory.")
            with st.form("form_save_inline_edits"):
                motivo_inline = st.text_input("Reason for edits (Required for Log) *", placeholder="Ex: Audit correction, P/N updated, transferred warehouse...")
                btn_save_inline = st.form_submit_button("💾 Save All Edits", use_container_width=True)
                
                if btn_save_inline:
                    if not motivo_inline.strip():
                        st.error("Reason is required to save changes.")
                    else:
                        c = conn.cursor()
                        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        
                        for orig, edit in mudancas:
                            id_peca = int(edit['ID'])
                            val_sp = limpar_dado(edit['Spare Part'])
                            val_pn = limpar_dado(edit['Part Number'])
                            val_sn = limpar_dado(edit['Serial Number'])
                            val_wh = limpar_dado(edit['Warehouse'])
                            val_sys = limpar_dado(edit['System'])
                            val_qtd = int(edit['Current Qty'])
                            
                            c.execute("UPDATE estoque SET spare_part=?, part_number=?, numero_serie=?, quantidade=?, estoque_origem=?, system=?, localizacao=? WHERE id=?",
                                      (val_sp, val_pn, val_sn, val_qtd, val_wh, val_sys, val_sys, id_peca))
                            
                            obs_mov = f"INLINE EDIT: {motivo_inline.strip()}"
                            sql_hist_edit = "INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                            c.execute(sql_hist_edit, (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "EDIT (ADMIN)", val_sp, val_pn, val_sn, val_qtd, val_wh, val_sys, "-", obs_mov))
                        
                        conn.commit()
                        st.success("All changes saved successfully!")
                        st.rerun()
                        
        st.markdown("---")
        with st.expander("🗑️ Remove Part from Main Inventory"):
            with st.form("form_remover_peca_main", clear_on_submit=True):
                col_rm1, col_rm2 = st.columns([1, 2])
                with col_rm1:
                    df_all_main = ler_banco("SELECT * FROM estoque")
                    if df_all_main.empty:
                        st.info("No parts available to remove.")
                        opcoes_rem_main = {}
                    else:
                        opcoes_rem_main = {}
                        for _, row in df_all_main.iterrows():
                            pn_text = f" | P/N: {row['part_number']}" if row['part_number'] else ""
                            sn_text = f" | S/N: {row['numero_serie']}" if row['numero_serie'] else ""
                            label = f"[{row['estoque_origem']}] {row['spare_part']}{pn_text}{sn_text} | Sys: {row['system']} (Qty: {row['quantidade']})"
                            opcoes_rem_main[label] = row['id']
                    
                    p_rem_label = st.selectbox("Select Part to Remove *", list(opcoes_rem_main.keys()) if opcoes_rem_main else ["No parts available"])
                with col_rm2:
                    p_rem_motivo = st.text_input("Reason for Removal *", placeholder="Ex: Item discontinued, duplicated entry, lost...")
                
                btn_rem_peca = st.form_submit_button("🗑️ Remove Part", use_container_width=True)
                if btn_rem_peca:
                    if not opcoes_rem_main:
                        st.error("No parts available to remove.")
                    elif not p_rem_motivo.strip():
                        st.error("A reason is required to remove a part.")
                    else:
                        id_p_rem = opcoes_rem_main[p_rem_label]
                        c = conn.cursor()
                        
                        c.execute("SELECT spare_part, part_number, numero_serie, estoque_origem, system, quantidade FROM estoque WHERE id = ?", (id_p_rem,))
                        part_info = c.fetchone()
                        
                        if part_info:
                            v_sp, v_pn, v_sn, v_wh, v_sys, v_qtd = part_info
                            
                            c.execute("DELETE FROM estoque WHERE id = ?", (id_p_rem,))
                            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            
                            obs_mov = f"REMOVED: {p_rem_motivo.strip()}"
                            c.execute("INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                      (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "DELETE (MAIN STOCK)", str(v_sp), str(v_pn), str(v_sn), int(v_qtd), str(v_wh), str(v_sys), "MAIN INVENTORY", obs_mov))
                            conn.commit()
                            st.success(f"Part '{v_sp}' was successfully removed!")
                            st.rerun()

    else:
        st.dataframe(styled_df_estoque, use_container_width=True, hide_index=True)

with abas[3]:
    st.subheader("Register New Item to Inventory")
    if st.session_state.perfil_atual != "ADMIN":
        st.error("🚫 Access Denied: Only Administrators can register new parts into inventory.")
    else:
        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                estoque_escolhido = st.selectbox("Select Warehouse *", ["Santa Catarina", "Duci", "Diego"])
                novo_spare = st.text_input("Spare Part Name *", placeholder="Ex: Central Board")
                novo_pn = st.text_input("Part Number (P/N)", placeholder="Ex: PN-55402")
            with col2:
                novo_sn = st.text_input("Serial Number (S/N)", placeholder="Optional (leave blank if batch)")
                nova_qtd = st.number_input("Initial Quantity *", min_value=1, step=1, value=1)
                novo_system = st.text_input("System *", placeholder="Ex: Fire Alarm SW2020")
            
            btn_cadastrar = st.form_submit_button("Save to Inventory", use_container_width=True)
            if btn_cadastrar:
                if not novo_spare.strip() or not novo_system.strip():
                    st.error("Spare Part Name and System are required.")
                else:
                    c = conn.cursor()
                    val_pn = novo_pn.strip() if novo_pn else ""
                    val_sn = novo_sn.strip() if novo_sn else ""
                    
                    c.execute("INSERT INTO estoque (spare_part, part_number, numero_serie, quantidade, estoque_origem, system, localizacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (novo_spare.strip(), val_pn, val_sn, int(nova_qtd), str(estoque_escolhido), novo_system.strip(), novo_system.strip()))
                    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    sql_hist_in = "INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    c.execute(sql_hist_in, (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "IN (REGISTRATION)", novo_spare.strip(), val_pn, val_sn, int(nova_qtd), str(estoque_escolhido), novo_system.strip(), "-", "-"))
                    conn.commit()
                    st.success(f"Part registered successfully in warehouse '{estoque_escolhido}'!")
                    st.rerun()

with abas[4]:
    st.subheader("Add / Restock Existing Parts")
    if st.session_state.perfil_atual != "ADMIN":
        st.error("🚫 Access Denied: Only Administrators can restock inventory.")
    else:
        df_todas_pecas = ler_banco("SELECT * FROM estoque")
        if df_todas_pecas.empty:
            st.info("No parts registered in inventory yet.")
        else:
            opcoes_reposicao = {}
            for _, row in df_todas_pecas.iterrows():
                pn_text = f" | P/N: {row['part_number']}" if row['part_number'] else ""
                sn_text = f" | S/N: {row['numero_serie']}" if row['numero_serie'] else ""
                label = f"[{row['estoque_origem']}] {row['spare_part']}{pn_text}{sn_text} | Sys: {row['system']} (Current: {row['quantidade']})"
                opcoes_reposicao[label] = row['id']
            
            with st.form("form_reposicao"):
                peca_rep_label = st.selectbox("Select Part to Restock", list(opcoes_reposicao.keys()))
                col_rq, col_rm = st.columns([1, 2])
                with col_rq:
                    qtd_adicional = st.number_input("Quantity to Add *", min_value=1, step=1, value=1)
                with col_rm:
                    motivo_reposicao = st.text_input("Reason / Invoice (Optional)", placeholder="Ex: Invoice #9982 or New Stock Arrival")
                
                btn_repor = st.form_submit_button("Add Stock Quantity", use_container_width=True)
                if btn_repor:
                    id_rep = opcoes_reposicao[peca_rep_label]
                    dados_rep = df_todas_pecas[df_todas_pecas['id'] == id_rep].iloc[0]
                    nova_qtd_total = int(dados_rep['quantidade'] + qtd_adicional)
                    
                    c = conn.cursor()
                    c.execute("UPDATE estoque SET quantidade = ? WHERE id = ?", (nova_qtd_total, int(id_rep)))
                    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    obs_mov = motivo_reposicao.strip() if motivo_reposicao.strip() else "Restock / Stock Addition"
                    
                    sql_hist_restock = "INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    c.execute(sql_hist_restock, (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "IN (RESTOCK)", str(dados_rep['spare_part']), str(dados_rep.get('part_number', '')), str(dados_rep.get('numero_serie', '')), int(qtd_adicional), str(dados_rep.get('estoque_origem', '')), str(dados_rep.get('system', '')), "-", obs_mov))
                    conn.commit()
                    st.success(f"Successfully added {qtd_adicional} unit(s) to '{dados_rep['spare_part']}'. New total: {nova_qtd_total}")
                    st.rerun()

with abas[5]:
    st.subheader("Tools (Cautela)")
    
    with st.form("form_add_tool"):
        st.markdown("#### Assign a New Tool")
        
        df_sys_tools = ler_banco("SELECT DISTINCT system FROM ferramentas UNION SELECT DISTINCT system FROM estoque ORDER BY system")
        lista_sys_tools = [s for s in df_sys_tools['system'].tolist() if s]
        opt_new_sys = "➕ New / Manual Entry"
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            t_nome = st.text_input("Tool Name / Description *", placeholder="Ex: Multimeter Fluke 115")
            t_id = st.text_input("Serial Number / Asset Tag (Optional)", placeholder="Ex: S/N 123456")
            col_tq1, col_tq2 = st.columns([1, 2])
            with col_tq1:
                t_qtd = st.number_input("Quantity *", min_value=0, step=1, value=1)
            with col_tq2:
                t_obs = st.text_input("Explanation (Required if Qty = 0)", placeholder="Why 0?")
        with col_t2:
            t_pn = st.text_input("Part Number (P/N) (Optional)", placeholder="Ex: 115-EUR")
            
            t_sys_sel = st.selectbox("System (Category) *", [opt_new_sys] + lista_sys_tools)
            if t_sys_sel == opt_new_sys:
                t_sys = st.text_input("Type System (Category) *", placeholder="Ex: Fire Alarm")
            else:
                t_sys = t_sys_sel
        
        btn_add_tool = st.form_submit_button("Assign Tool to Me", use_container_width=True)
        if btn_add_tool:
            if not t_nome.strip() or not t_sys.strip():
                st.error("Tool Name and System are required.")
            elif t_qtd == 0 and not t_obs.strip():
                st.error("An explanation is required when assigning a tool with 0 quantity.")
            else:
                c = conn.cursor()
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                c.execute("INSERT INTO ferramentas (ferramenta, part_number, identificacao, usuario, data_retirada, status, system, quantidade, observacao) VALUES (?, ?, ?, ?, ?, 'EM POSSE', ?, ?, ?)",
                          (t_nome.strip(), t_pn.strip() if t_pn else "", t_id.strip() if t_id else "", str(st.session_state.usuario_atual), agora, t_sys.strip(), int(t_qtd), t_obs.strip()))
                conn.commit()
                st.success("Tool added to your cautela!")
                st.rerun()
                
    st.markdown("---")
    st.markdown("#### Tools in Possession")
    
    df_users_tools = ler_banco("SELECT username, nome_completo FROM usuarios ORDER BY nome_completo")
    dict_users = {f"{r['nome_completo']} ({r['username']})": r['username'] for _, r in df_users_tools.iterrows()}
    
    default_idx = 0
    for idx, key in enumerate(dict_users.keys()):
        if dict_users[key] == st.session_state.usuario_atual:
            default_idx = idx
            break
            
    user_selecionado_label = st.selectbox("Select Technician to View Tools:", list(dict_users.keys()), index=default_idx)
    user_selecionado = dict_users[user_selecionado_label]
    
    df_my_tools = ler_banco("SELECT id AS 'ID', system AS 'System', ferramenta AS 'Tool Name', part_number AS 'Part Number', identificacao AS 'Identification', quantidade AS 'Qty', observacao AS 'Observation', data_retirada AS 'Date Assigned', status AS 'Status' FROM ferramentas WHERE usuario = ? AND status = 'EM POSSE' ORDER BY system, ferramenta", (str(user_selecionado),))
    
    if df_my_tools.empty:
        st.info(f"No tools currently assigned to {user_selecionado_label}.")
    else:
        pode_editar = (user_selecionado == st.session_state.usuario_atual) or (st.session_state.perfil_atual == "ADMIN")
        
        if pode_editar:
            st.caption("Change the status to 'DEVOLVIDA' and click confirm to return a tool.")
            edited_tools = st.data_editor(
                df_my_tools,
                use_container_width=True,
                hide_index=True,
                disabled=["ID", "System", "Tool Name", "Part Number", "Identification", "Qty", "Observation", "Date Assigned"],
                column_config={
                    "Status": st.column_config.SelectboxColumn("Status", options=["EM POSSE", "DEVOLVIDA"], required=True)
                }
            )
            
            mudancas_ferramentas = []
            for i in range(len(df_my_tools)):
                if df_my_tools.iloc[i]['Status'] != edited_tools.iloc[i]['Status']:
                    mudancas_ferramentas.append(edited_tools.iloc[i])
                    
            if mudancas_ferramentas:
                if st.button("Confirm Tool Returns", use_container_width=True):
                    c = conn.cursor()
                    for edit in mudancas_ferramentas:
                        c.execute("UPDATE ferramentas SET status = ? WHERE id = ?", (str(edit['Status']), int(edit['ID'])))
                    conn.commit()
                    st.success("Tools status updated successfully!")
                    st.rerun()
        else:
            st.dataframe(df_my_tools, use_container_width=True, hide_index=True)

with abas[6]:
    st.subheader("Service Checkouts (Usage on Vessel)")
    busca_out = st.text_input("Filter checkouts by vessel, SG/WO, technician, part, P/N, warehouse or system...", key="search_out")
    df_out = ler_banco("SELECT data_hora AS 'Date/Time', usuario AS 'Technician', estoque_origem AS 'Warehouse', spare_part AS 'Spare Part', part_number AS 'Part Number', numero_serie AS 'Serial Number', quantidade AS 'Qty', system AS 'System', navio AS 'Vessel', work_order AS 'SG / WO' FROM historico WHERE tipo_movimento LIKE 'OUT (SERVICE)%' OR tipo_movimento = 'OUT (VESSEL SERVICE)' ORDER BY id DESC")
    if busca_out:
        bo_lower = busca_out.lower()
        f_out = (
            df_out['Vessel'].str.lower().str.contains(bo_lower, na=False) |
            df_out['SG / WO'].str.lower().str.contains(bo_lower, na=False) |
            df_out['Technician'].str.lower().str.contains(bo_lower, na=False) |
            df_out['Warehouse'].str.lower().str.contains(bo_lower, na=False) |
            df_out['Spare Part'].str.lower().str.contains(bo_lower, na=False) |
            df_out['Part Number'].str.lower().str.contains(bo_lower, na=False) |
            df_out['System'].str.lower().str.contains(bo_lower, na=False)
        )
        df_out = df_out[f_out]
    st.dataframe(df_out, use_container_width=True, hide_index=True)

with abas[7]:
    st.subheader("Full Usage History")
    busca_hist = st.text_input("Filter full history by vessel, SG/WO, technician, part, P/N, warehouse or system...", key="search_full")
    df_hist = ler_banco("SELECT data_hora AS 'Date/Time', usuario AS 'Technician', tipo_movimento AS 'Movement', estoque_origem AS 'Warehouse', spare_part AS 'Spare Part', part_number AS 'Part Number', numero_serie AS 'Serial Number', quantidade AS 'Qty', system AS 'System', navio AS 'Vessel', work_order AS 'SG / WO' FROM historico ORDER BY id DESC")
    if busca_hist:
        bh_lower = busca_hist.lower()
        f_hist = (
            df_hist['Vessel'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['SG / WO'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['Technician'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['Warehouse'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['Spare Part'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['Part Number'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['System'].str.lower().str.contains(bh_lower, na=False)
        )
        df_hist = df_hist[f_hist]
    st.dataframe(df_hist, use_container_width=True, hide_index=True)

with abas[8]:
    st.subheader("Account Settings")
    c = conn.cursor()
    c.execute("SELECT nome_completo, email FROM usuarios WHERE username = ?", (str(st.session_state.usuario_atual),))
    dados_meu_user = c.fetchone()
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        with st.form("form_dados_pessoais"):
            st.markdown("#### Personal Data")
            st.text_input("Username", value=st.session_state.usuario_atual, disabled=True)
            novo_nome_perfil = st.text_input("Full Name", value=dados_meu_user[0] if dados_meu_user else "")
            novo_email_perfil = st.text_input("Professional Email", value=dados_meu_user[1] if dados_meu_user else "")
            if st.form_submit_button("Update Data", use_container_width=True):
                if not validar_email_profissional(novo_email_perfil):
                    st.error("Please provide a valid professional corporate email.")
                else:
                    c.execute("UPDATE usuarios SET nome_completo = ?, email = ? WHERE username = ?",
                              (novo_nome_perfil.strip(), novo_email_perfil.strip().lower(), str(st.session_state.usuario_atual)))
                    conn.commit()
                    st.session_state.nome_atual = novo_nome_perfil.strip()
                    st.success("Data updated successfully!")
                    st.rerun()
    with col_p2:
        with st.form("form_trocar_senha", clear_on_submit=True):
            st.markdown("#### Change Password")
            senha_atual_input = st.text_input("Current Password *", type="password")
            senha_nova_1 = st.text_input("New Password *", type="password")
            senha_nova_2 = st.text_input("Confirm New Password *", type="password")
            if st.form_submit_button("Confirm New Password", use_container_width=True):
                c.execute("SELECT senha_hash FROM usuarios WHERE username = ?", (str(st.session_state.usuario_atual),))
                hash_atual_bd = c.fetchone()[0]
                if hash_senha(senha_atual_input) != hash_atual_bd:
                    st.error("Incorrect current password.")
                elif len(senha_nova_1) < 4:
                    st.error("Password must be at least 4 characters long.")
                elif senha_nova_1 != senha_nova_2:
                    st.error("New passwords do not match.")
                else:
                    c.execute("UPDATE usuarios SET senha_hash = ?, pedido_reset = 0 WHERE username = ?",
                              (hash_senha(senha_nova_1), str(st.session_state.usuario_atual)))
                    conn.commit()
                    st.success("Password changed successfully!")

if st.session_state.perfil_atual == "ADMIN":
    with abas[9]:
        st.subheader("Administrator Panel - User Management")
        c_adm = conn.cursor()
        c_adm.execute("SELECT id, username, nome_completo, email, perfil, status, data_cadastro, pedido_reset FROM usuarios ORDER BY status DESC, pedido_reset DESC, id ASC")
        users_rows = c_adm.fetchall()
        
        pendentes_lista = [r for r in users_rows if r[5] == 'PENDENTE' or r[7] == 1]
        
        if pendentes_lista:
            st.markdown("### Pending Approvals & Password Resets")
            for u_row in pendentes_lista:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                    with c1:
                        st.markdown(f"**{u_row[2]}** (`{u_row[1]}`)")
                        st.caption(f"Email: {u_row[3]} | Status: {u_row[5]}")
                    with c2:
                        if u_row[5] == 'PENDENTE':
                            st.warning("Pending Approval")
                        if u_row[7] == 1:
                            st.error("Requested Password Reset")
                    with c3:
                        if u_row[5] == 'PENDENTE':
                            if st.button(f"Approve {u_row[1]}", key=f"aprov_{u_row[0]}", use_container_width=True):
                                c_adm.execute("UPDATE usuarios SET status = 'APROVADO' WHERE id = ?", (int(u_row[0]),))
                                conn.commit()
                                st.success(f"User {u_row[1]} approved!")
                                st.rerun()
                    with c4:
                        if st.button(f"Reset Pass to 1234", key=f"rst_{u_row[0]}", use_container_width=True):
                            c_adm.execute("UPDATE usuarios SET senha_hash = ?, pedido_reset = 0 WHERE id = ?", (hash_senha("1234"), int(u_row[0])))
                            conn.commit()
                            st.success(f"Password reset for {u_row[1]}!")
                            st.rerun()
                            
        st.markdown("---")
        st.markdown("### Global Tools Management (All Technicians)")
        df_all_tools = ler_banco("SELECT f.id AS 'ID', u.nome_completo AS 'Technician', f.system AS 'System', f.ferramenta AS 'Tool Name', f.part_number AS 'Part Number', f.identificacao AS 'Identification', f.quantidade AS 'Qty', f.observacao AS 'Observation', f.data_retirada AS 'Date Assigned', f.status AS 'Status' FROM ferramentas f JOIN usuarios u ON f.usuario = u.username ORDER BY f.status DESC, f.system, f.data_retirada DESC")
        if df_all_tools.empty:
            st.info("No tools currently assigned to any technicians.")
        else:
            st.dataframe(df_all_tools, use_container_width=True, hide_index=True)
            
        st.markdown("---")
        st.markdown("### All Registered Users & Management")
        
        df_users_full = pd.DataFrame(users_rows, columns=['ID', 'Username', 'Full Name', 'Email', 'Role', 'Status', 'Registration Date', 'Reset Flag'])
        st.dataframe(df_users_full[['ID', 'Username', 'Full Name', 'Email', 'Role', 'Status', 'Registration Date']], use_container_width=True, hide_index=True)
        
        col_edit, col_rem = st.columns(2)
        
        with col_edit:
            st.markdown("#### Edit User Account")
            with st.form("form_gerenciar_user_completo"):
                opcoes_u = {f"{r[2]} ({r[1]}) - Status: {r[5]} - Role: {r[4]}": r[0] for r in users_rows}
                user_sel_label = st.selectbox("Select User to Modify", list(opcoes_u.keys()))
                
                novo_status_sel = st.selectbox("Change Status", ["APROVADO", "PENDENTE", "BLOQUEADO"])
                novo_perfil_sel = st.selectbox("Change Role", ["TECNICO", "ADMIN"])
                nova_senha_adm = st.text_input("Set New Password Manually (Optional)", type="password", placeholder="Leave blank to keep current")
                
                btn_salvar_adm = st.form_submit_button("Save User Changes", use_container_width=True)
                if btn_salvar_adm:
                    id_u_alvo = int(opcoes_u[user_sel_label])
                    if nova_senha_adm.strip():
                        c_adm.execute("UPDATE usuarios SET status = ?, perfil = ?, senha_hash = ?, pedido_reset = 0 WHERE id = ?", 
                                      (novo_status_sel, novo_perfil_sel, hash_senha(nova_senha_adm.strip()), id_u_alvo))
                    else:
                        c_adm.execute("UPDATE usuarios SET status = ?, perfil = ? WHERE id = ?", 
                                      (novo_status_sel, novo_perfil_sel, id_u_alvo))
                    conn.commit()
                    st.success("User updated successfully!")
                    st.rerun()
                    
        with col_rem:
            st.markdown("#### Remove User Account")
            with st.form("form_remover_usuario"):
                opcoes_rem = {f"{r[2]} ({r[1]})": r[0] for r in users_rows if r[1].lower() != 'admin'}
                
                if not opcoes_rem:
                    st.info("No removable users available.")
                    user_rem_label = None
                else:
                    user_rem_label = st.selectbox("Select User to Delete", list(opcoes_rem.keys()))
                
                st.warning("⚠️ Warning: Deletion is permanent. Only the master 'admin' account is protected.")
                btn_remover = st.form_submit_button("🗑️ Permanently Delete User", use_container_width=True)
                
                if btn_remover and user_rem_label:
                    id_u_rem = int(opcoes_rem[user_rem_label])
                    c_adm.execute("DELETE FROM usuarios WHERE id = ?", (id_u_rem,))
                    conn.commit()
                    st.success("User successfully removed from system!")
                    st.rerun()
