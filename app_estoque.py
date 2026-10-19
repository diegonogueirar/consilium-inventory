import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import base64
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText

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
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-image: url("data:image/png;base64,{data}");
            background-repeat: no-repeat;
            background-position: center;
            background-size: 75vw auto;
            opacity: 0.045;
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

def iniciar_banco():
    conn = sqlite3.connect("estoque_empresa.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS estoque (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spare_part TEXT NOT NULL,
                    part_number TEXT,
                    numero_serie TEXT,
                    quantidade INTEGER NOT NULL,
                    estoque_origem TEXT NOT NULL,
                    system TEXT NOT NULL
                )''')
    
    colunas_estoque = [col[1] for col in c.execute("PRAGMA table_info(estoque)").fetchall()]
    if 'part_number' not in colunas_estoque:
        c.execute("ALTER TABLE estoque ADD COLUMN part_number TEXT")
    if 'estoque_origem' not in colunas_estoque:
        c.execute("ALTER TABLE estoque ADD COLUMN estoque_origem TEXT DEFAULT 'Santa Catarina'")
    if 'system' not in colunas_estoque:
        c.execute("ALTER TABLE estoque ADD COLUMN system TEXT DEFAULT 'General'")

    c.execute('''CREATE TABLE IF NOT EXISTS historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_hora TEXT NOT NULL,
                    usuario TEXT NOT NULL,
                    tipo_movimento TEXT NOT NULL,
                    spare_part TEXT NOT NULL,
                    part_number TEXT,
                    numero_serie TEXT,
                    quantidade INTEGER NOT NULL,
                    estoque_origem TEXT,
                    system TEXT,
                    navio TEXT,
                    work_order TEXT
                )''')
    
    colunas_hist = [col[1] for col in c.execute("PRAGMA table_info(historico)").fetchall()]
    if 'part_number' not in colunas_hist:
        c.execute("ALTER TABLE historico ADD COLUMN part_number TEXT")
    if 'estoque_origem' not in colunas_hist:
        c.execute("ALTER TABLE historico ADD COLUMN estoque_origem TEXT")
    if 'system' not in colunas_hist:
        c.execute("ALTER TABLE historico ADD COLUMN system TEXT")

    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    nome_completo TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    senha_hash TEXT NOT NULL,
                    perfil TEXT NOT NULL DEFAULT 'TECNICO',
                    status TEXT NOT NULL DEFAULT 'PENDENTE',
                    data_cadastro TEXT NOT NULL,
                    pedido_reset INTEGER DEFAULT 0
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS config_email (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    smtp_server TEXT,
                    smtp_port INTEGER,
                    email_remetente TEXT,
                    senha_app TEXT
                )''')
    
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.execute("SELECT COUNT(*) FROM usuarios WHERE perfil = 'ADMIN'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT OR IGNORE INTO usuarios (username, nome_completo, email, senha_hash, perfil, status, data_cadastro) VALUES (?, ?, ?, ?, 'ADMIN', 'APROVADO', ?)",
                  ('admin', 'General Administrator', 'admin@consilium.com', hash_senha('1234'), agora))
    
    conn.commit()
    return conn

conn = iniciar_banco()

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
                    c.execute("SELECT username, nome_completo, senha_hash, perfil, status FROM usuarios WHERE LOWER(username) = ? OR LOWER(email) = ?", (usuario_input, usuario_input))
                    user_row = c.fetchone()
                    if not user_row:
                        st.error("User or email not found.")
                    elif user_row[2] != hash_senha(senha_input):
                        st.error("Incorrect password.")
                    elif user_row[4] == "PENDENTE":
                        st.warning("Your account is pending Administrator approval.")
                    elif user_row[4] == "BLOQUEADO":
                        st.error("Account deactivated.")
                    else:
                        st.session_state.logado = True
                        st.session_state.usuario_atual = user_row[0]
                        st.session_state.nome_atual = user_row[1]
                        st.session_state.perfil_atual = user_row[3]
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
                        except sqlite3.IntegrityError:
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
                        enviado, _ = enviar_email_recuperacao(email_rec, u_rec[1], senha_temp)
                        if enviado:
                            c.execute("UPDATE usuarios SET senha_hash = ?, pedido_reset = 0 WHERE id = ?", (hash_senha(senha_temp), u_rec[0]))
                            conn.commit()
                            st.success("Temporary password sent to your email.")
                        else:
                            c.execute("UPDATE usuarios SET pedido_reset = 1 WHERE id = ?", (u_rec[0],))
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
        st.session_state.logado = False
        st.rerun()

if st.session_state.perfil_atual == "ADMIN":
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM usuarios WHERE status = 'PENDENTE' OR pedido_reset = 1")
    pendencias = c.fetchone()[0]
    if pendencias > 0:
        st.warning(f"Attention Administrator: There are {pendencias} pending request(s) in the Admin Panel tab.")

df_est_total = pd.read_sql_query("SELECT * FROM estoque", conn)
df_hist_total = pd.read_sql_query("SELECT * FROM historico WHERE tipo_movimento = 'OUT (SERVICE)'", conn)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Registered Models", len(df_est_total))
k2.metric("Available Parts", int(df_est_total['quantidade'].sum()) if not df_est_total.empty else 0)
k3.metric("Zeroed Parts", len(df_est_total[df_est_total['quantidade'] == 0]) if not df_est_total.empty else 0)
k4.metric("Vessel Dispatches", len(df_hist_total))

st.write("")

lista_abas = ["Checkout Parts", "Check Inventory", "Register Part", "Add/Restock Parts", "Usage History", "My Profile"]
if st.session_state.perfil_atual == "ADMIN":
    lista_abas.append("Admin Panel")

abas = st.tabs(lista_abas)

with abas[0]:
    st.subheader("Register Part Usage on Vessel")
    df_disponivel = pd.read_sql_query("SELECT * FROM estoque WHERE quantidade > 0", conn)
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
    st.subheader("Inventory Lookup")
    busca = st.text_input("Search (Partial characters allowed, e.g., part name, P/N, S/N, warehouse or system)...")
    df_estoque = pd.read_sql_query("SELECT id AS 'ID', estoque_origem AS 'Warehouse', spare_part AS 'Spare Part', part_number AS 'Part Number', numero_serie AS 'Serial Number', quantidade AS 'Current Qty', system AS 'System' FROM estoque", conn)
    if busca:
        busca_lower = busca.lower()
        filtro = (
            df_estoque['Warehouse'].str.lower().str.contains(busca_lower, na=False) |
            df_estoque['Spare Part'].str.lower().str.contains(busca_lower, na=False) |
            df_estoque['Part Number'].str.lower().str.contains(busca_lower, na=False) |
            df_estoque['Serial Number'].str.lower().str.contains(busca_lower, na=False) |
            df_estoque['System'].str.lower().str.contains(busca_lower, na=False)
        )
        df_estoque = df_estoque[filtro]
    st.dataframe(df_estoque, use_container_width=True, hide_index=True)

with abas[2]:
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
                    c.execute("INSERT INTO estoque (spare_part, part_number, numero_serie, quantidade, estoque_origem, system) VALUES (?, ?, ?, ?, ?, ?)",
                              (novo_spare.strip(), novo_pn.strip(), novo_sn.strip(), int(nova_qtd), estoque_escolhido, novo_system.strip()))
                    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    sql_hist_in = "INSERT INTO historico (data_hora, usuario, tipo_movimento, spare_part, part_number, numero_serie, quantidade, estoque_origem, system, navio, work_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    c.execute(sql_hist_in, (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "IN (REGISTRATION)", novo_spare.strip(), novo_pn.strip(), novo_sn.strip(), int(nova_qtd), estoque_escolhido, novo_system.strip(), "-", "-"))
                    conn.commit()
                    st.success(f"Part registered successfully in warehouse '{estoque_escolhido}'!")
                    st.rerun()

with abas[3]:
    st.subheader("Add / Restock Existing Parts")
    if st.session_state.perfil_atual != "ADMIN":
        st.error("🚫 Access Denied: Only Administrators can restock inventory.")
    else:
        df_todas_pecas = pd.read_sql_query("SELECT * FROM estoque", conn)
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
                    c.execute(sql_hist_restock, (agora, f"{st.session_state.nome_atual} ({st.session_state.usuario_atual})", "IN (RESTOCK)", dados_rep['spare_part'], dados_rep.get('part_number', ''), dados_rep.get('numero_serie', ''), int(qtd_adicional), dados_rep.get('estoque_origem', ''), dados_rep.get('system', ''), "-", obs_mov))
                    conn.commit()
                    st.success(f"Successfully added {qtd_adicional} unit(s) to '{dados_rep['spare_part']}'. New total: {nova_qtd_total}")
                    st.rerun()

with abas[4]:
    st.subheader("Usage History")
    busca_hist = st.text_input("Filter history by vessel, WO, technician, part, P/N, warehouse or system...")
    df_hist = pd.read_sql_query("SELECT data_hora AS 'Date/Time', usuario AS 'Technician', tipo_movimento AS 'Movement', estoque_origem AS 'Warehouse', spare_part AS 'Spare Part', part_number AS 'Part Number', numero_serie AS 'Serial Number', quantidade AS 'Qty', system AS 'System', navio AS 'Vessel', work_order AS 'Work Order' FROM historico ORDER BY id DESC", conn)
    if busca_hist:
        bh_lower = busca_hist.lower()
        f_hist = (
            df_hist['Vessel'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['Work Order'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['Technician'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['Warehouse'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['Spare Part'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['Part Number'].str.lower().str.contains(bh_lower, na=False) |
            df_hist['System'].str.lower().str.contains(bh_lower, na=False)
        )
        df_hist = df_hist[f_hist]
    st.dataframe(df_hist, use_container_width=True, hide_index=True)

with abas[5]:
    st.subheader("Account Settings")
    c = conn.cursor()
    c.execute("SELECT nome_completo, email FROM usuarios WHERE username = ?", (st.session_state.usuario_atual,))
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
                              (novo_nome_perfil.strip(), novo_email_perfil.strip().lower(), st.session_state.usuario_atual))
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
                c.execute("SELECT senha_hash FROM usuarios WHERE username = ?", (st.session_state.usuario_atual,))
                hash_atual_bd = c.fetchone()[0]
                if hash_senha(senha_atual_input) != hash_atual_bd:
                    st.error("Incorrect current password.")
                elif len(senha_nova_1) < 4:
                    st.error("Password must be at least 4 characters long.")
                elif senha_nova_1 != senha_nova_2:
                    st.error("New passwords do not match.")
                else:
                    c.execute("UPDATE usuarios SET senha_hash = ?, pedido_reset = 0 WHERE username = ?",
                              (hash_senha(senha_nova_1), st.session_state.usuario_atual))
                    conn.commit()
                    st.success("Password changed successfully!")

if st.session_state.perfil_atual == "ADMIN":
    with abas[6]:
        st.subheader("Administrator Panel - User & Inventory Management")
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
        st.markdown("### Edit Part Warehouse (Transfer Location)")
        df_pecas_adm = pd.read_sql_query("SELECT id, spare_part, part_number, estoque_origem, system FROM estoque", conn)
        if df_pecas_adm.empty:
            st.info("No parts available to edit.")
        else:
            with st.form("form_mudar_warehouse"):
                opcoes_wh = {f"[{r['estoque_origem']}] {r['spare_part']} (P/N: {r['part_number'] or 'N/A'}) - Sys: {r['system']}": r['id'] for _, r in df_pecas_adm.iterrows()}
                peca_sel_wh = st.selectbox("Select Part to Transfer", list(opcoes_wh.keys()))
                novo_wh_escolhido = st.selectbox("New Warehouse", ["Santa Catarina", "Duci", "Diego"])
                
                btn_salvar_wh = st.form_submit_button("Update Part Warehouse", use_container_width=True)
                if btn_salvar_wh:
                    id_peca_wh = opcoes_wh[peca_sel_wh]
                    c_adm.execute("UPDATE estoque SET estoque_origem = ? WHERE id = ?", (novo_wh_escolhido, int(id_peca_wh)))
                    conn.commit()
                    st.success(f"Warehouse successfully updated to '{novo_wh_escolhido}'!")
                    st.rerun()

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
