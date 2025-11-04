import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import csv, os, hashlib, datetime, random, math
from tkcalendar import Calendar
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Tropa foi adcionado mais comentarios para as nova seção que eu criei, se vc tive lendo e tiver com duvida pode manda msg

# -------------- Config / Arquivos ----------------
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
PROGRESS_FILE = os.path.join(DATA_DIR, "progresso.csv")
TASKS_FILE = os.path.join(DATA_DIR, "tarefas.csv")
REWARDS_FILE = os.path.join(DATA_DIR, "recompensas.csv")  # novo arquivo para recompensas

os.makedirs(DATA_DIR, exist_ok=True)

# cria csvs iniciais se não existirem (mesma lógica original)
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # adicionei essas coluna 'rewards' para registrar recompensas resgatadas pelo usuário
        writer.writerow(["email", "senha", "nome", "pontos", "nivel", "ultimo_login", "badges", "rewards"])

if not os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["email", "data", "tarefa", "pontos", "relatorio"])

if not os.path.exists(TASKS_FILE):
    with open(TASKS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nivel", "tarefa", "descricao", "pontos_minimo", "pontos_maximo"])
        default_tasks = [
            ["Básico", "Coleta Seletiva", "Separe papel, plástico, metal e vidro corretamente.", 15, 25],
            ["Básico", "Economia de Água", "Faça um banho de até 10 minutos.", 15, 25],
            ["Básico", "Economia de Energia", "Desligue eletrodomésticos não usados por 24h.", 15, 25],
            ["Intermediário", "Horta Caseira", "Plante uma muda e registre o crescimento.", 30, 50],
            ["Intermediário", "Compostagem", "Inicie compostagem de restos orgânicos.", 35, 50],
            ["Avançado", "Projeto de Impacto", "Crie um projeto sustentável na comunidade.", 60, 80],
        ]
        writer.writerows(default_tasks)

# esse bloco aqui cria arquivo de recompensas padrão se não existir
if not os.path.exists(REWARDS_FILE):
    with open(REWARDS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # colunas: id, nivel, titulo, descricao, custo_pontos
        writer.writerow(["id", "nivel", "titulo", "descricao", "custo_pontos"])
        default_rewards = [
            ["R_BASIC_01", "Básico", "Garrafa Ecológica Virtual", "Um troféu virtual e destaque no perfil - celebra seu comprometimento inicial.", "50"],
            ["R_BASIC_02", "Básico", "Kit Dicas Sustentáveis", "Guia com 10 dicas práticas para economia de água e energia.", "40"],
            ["R_INTER_01", "Intermediário", "Certificado de Ação Sustentável", "Certificado digital que pode ser compartilhado em redes sociais.", "150"],
            ["R_INTER_02", "Intermediário", "Adesivo 'Engajado' Virtual", "Selo visual especial para o perfil e ranking.", "120"],
            ["R_ADV_01", "Avançado", "Embaixador Verde", "Título especial que aparece no topo do ranking e distinção no perfil.", "300"],
            ["R_ADV_02", "Avançado", "Workshop Online (Simulado)", "Convite simbólico para workshop temático (simulação interna).", "350"],
        ]
        writer.writerows(default_rewards)

# ------------------ Utils -------------------------
def md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def carregar_usuarios():
    users = {}
    # isso e para lidar com header antigo ou novo: DictReader retornará apenas colunas presentes.
    with open(USER_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # garantir que chaves essenciais existam e preencher defaults
            if "rewards" not in row:
                row["rewards"] = ""  # lista de ids de recompensas resgatadas separadas por ';'
            if "badges" not in row:
                row["badges"] = ""
            users[row["email"]] = row
    return users

def salvar_usuarios_dict(users: dict):
    with open(USER_FILE, "w", newline="", encoding="utf-8") as f:
        # agora gravamos com a coluna 'rewards' também
        fieldnames = ["email", "senha", "nome", "pontos", "nivel", "ultimo_login", "badges", "rewards"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for u in users.values():
            # essa fita aqui e para garantir chaves existam antes de escrever
            row = {
                "email": u.get("email",""),
                "senha": u.get("senha",""),
                "nome": u.get("nome",""),
                "pontos": u.get("pontos","0"),
                "nivel": u.get("nivel","Básico"),
                "ultimo_login": u.get("ultimo_login", ""),
                "badges": u.get("badges", ""),
                "rewards": u.get("rewards", "")
            }
            writer.writerow(row)

def definir_nivel(pontos: int) -> str:
    if pontos < 100:
        return "Básico"
    elif pontos < 300:
        return "Intermediário"
    else:
        return "Avançado"

def pontos_para_proximo_nivel(pontos: int):
    # simples referência de transição; pode ajustar conforme relatório.
    if pontos < 100:
        return 100 - pontos
    elif pontos < 300:
        return 300 - pontos
    else:
        return 0

def salvar_progresso(email, tarefa, pontos, relatorio):
    with open(PROGRESS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([email, str(datetime.date.today()), tarefa, pontos, relatorio])

def obter_tarefas_por_nivel(nivel):
    tasks = []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["nivel"] == nivel:
                tasks.append(row)
    return tasks

def contar_tarefas_dia(email, date=None):
    if date is None:
        date = str(datetime.date.today())
    count = 0
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["email"] == email and row["data"] == date:
                    count += 1
    except FileNotFoundError:
        return 0
    return count

def adicionar_badge(usuario: dict, nivel: str):
    badges_map = {
        "Básico": "🌱 Consciente",
        "Intermediário": "♻️ Engajado",
        "Avançado": "🌍 Sustentável"
    }
    badge = badges_map.get(nivel, "")
    if not usuario.get("badges"):
        usuario["badges"] = badge
    elif badge not in usuario["badges"]:
        usuario["badges"] += f", {badge}"

# -------- Recompensas (novas funções) que foi adcionado recentemente  ----------
def carregar_recompensas():
    rewards = []
    with open(REWARDS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["custo_pontos"] = int(row["custo_pontos"])
            rewards.append(row)
    return rewards

def obter_recompensa_por_id(rid):
    with open(REWARDS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] == rid:
                row["custo_pontos"] = int(row["custo_pontos"])
                return row
    return None

def usuario_tem_resgatado(usuario, reward_id):
    rewards = usuario.get("rewards", "")
    if not rewards:
        return False
    return reward_id in [r for r in rewards.split(";") if r]

def resgatar_recompensa_para_usuario(usuario_email, reward_id):
    users = carregar_usuarios()
    if usuario_email not in users:
        return False, "Usuário não encontrado."
    u = users[usuario_email]
    recompensa = obter_recompensa_por_id(reward_id)
    if not recompensa:
        return False, "Recompensa inválida."
    pontos = int(u.get("pontos", "0"))
    # verifica nivel
    nivel_usuario = u.get("nivel","Básico")
    niveis_ordem = {"Básico": 0, "Intermediário": 1, "Avançado": 2}
    if niveis_ordem.get(nivel_usuario,0) < niveis_ordem.get(recompensa["nivel"],0):
        return False, f"Recompensa disponível apenas para nível {recompensa['nivel']} ou superior."
    if pontos < recompensa["custo_pontos"]:
        return False, "Pontos insuficientes para resgatar essa recompensa."
    # verifica se já resgatou
    if usuario_tem_resgatado(u, reward_id):
        return False, "Você já resgatou essa recompensa."
    # desconta pontos e marca recomp
    u["pontos"] = str(pontos - recompensa["custo_pontos"])
    existing = u.get("rewards", "")
    if existing and existing.strip():
        u["rewards"] = existing + ";" + reward_id
    else:
        u["rewards"] = reward_id
    # opcional: ao resgatar, conceder um badge extra? (não por enquanto)
    users[usuario_email] = u
    salvar_usuarios_dict(users)
    return True, f"Recompensa '{recompensa['titulo']}' resgatada! -{recompensa['custo_pontos']} pts"

# ---------- UI helper: hover / card -------------
def with_hover(widget, enter_bg=None, leave_bg=None):
    def on_enter(e):
        if enter_bg:
            try: widget.configure(bg=enter_bg)
            except: pass
    def on_leave(e):
        if leave_bg:
            try: widget.configure(bg=leave_bg)
            except: pass
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

# ------------- Classe principal (UI) -------------
class GreenPlusPro:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Green+")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 640)
        self.usuario = None

        #  paleta atualizada (tons suaves)
        self.colors = {
            "primary": "#0f6b3a",      # verde esmeralda
            "accent": "#39b683",       # verde claro
            "bg": "#f4fbf6",           # fundo suave
            "card": "#ffffff",
            "muted": "#6f6f6f",
            "danger": "#d9534f",
            "topbar": "#eaf6ef"
        }
        self.root.configure(bg=self.colors["bg"])
        self.style = ttk.Style()
        self._setup_styles()
        self._create_layout()
        self.show_login()

    def _setup_styles(self):
        s = self.style
        # tente um theme moderno caso exista
        try:
            s.theme_use("clam")
        except:
            pass
        # geral
        default_font = ("Segoe UI", 10)
        s.configure('.', font=default_font)

        # Botões
        s.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
        s.map("TButton",
              background=[('active', self.colors['accent'])],
              foreground=[('disabled', '#9a9a9a')])

        s.configure("Accent.TButton", background=self.colors['accent'], foreground='white', font=("Segoe UI", 10, "bold"))
        s.configure("Danger.TButton", foreground='white', background=self.colors['danger'])

        # Labels
        s.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=self.colors['primary'], background=self.colors['bg'])
        s.configure("SubHeader.TLabel", font=("Segoe UI", 12, "bold"), foreground=self.colors['primary'], background=self.colors['bg'])
        s.configure("Card.TFrame", background=self.colors['card'])
        s.configure("CardHeader.TLabel", font=("Segoe UI", 11, "bold"), background=self.colors['card'])
        s.configure("Muted.TLabel", font=("Segoe UI", 10), foreground=self.colors['muted'], background=self.colors['card'])

        # Progressbar
        s.configure("green.Horizontal.TProgressbar", troughcolor=self.colors['topbar'], background=self.colors['accent'], thickness=12)

    def _create_layout(self):
        # Sidebar — agora usando ttk.Frame visual
        self.sidebar = tk.Frame(self.root, bg=self.colors["primary"], width=260)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.sidebar, text="🌿  Green+", bg=self.colors["primary"], fg="white",
                 font=("Segoe UI", 20, "bold")).pack(pady=(18,2), padx=18)
        tk.Label(self.sidebar, text="Transforme hábitos em impacto", bg=self.colors["primary"], fg="#dff3e6",
                 font=("Segoe UI", 9)).pack(pady=(0,12), padx=18)

        # Menu items (ttk.Button para consistência)
        menu_items = [
            ("Dashboard", self.show_dashboard, "📊"),
            ("Tarefas", self.show_tasks, "📝"),
            ("Calendário", self.show_calendar, "📅"),
            ("Histórico", self.show_history, "📖"),
            ("Ranking", self.show_ranking, "🏆"),
            ("Conquistas", self.show_achievements, "🎖️"),
            ("Recompensas", self.show_rewards_public, "🎁"),
            ("Perfil", self.show_profile, "👤"),
            ("Sair", self.logout, "🚪"),
        ]
        for text, cmd, ico in menu_items:
            b = tk.Button(self.sidebar, text=f"  {ico}  {text}", anchor="w", bg=self.colors["primary"], fg="white",
                          bd=0, relief=tk.FLAT, font=("Segoe UI", 11), command=cmd, cursor="hand2", activebackground="#0f7a45")
            b.pack(fill=tk.X, padx=14, pady=8)

        # Corpo
        self.body = tk.Frame(self.root, bg=self.colors["bg"])
        self.body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Topbar
        self.topbar = tk.Frame(self.body, bg=self.colors["topbar"], height=72)
        self.topbar.pack(fill=tk.X, padx=20, pady=(12,6))
        self.topbar_left = tk.Frame(self.topbar, bg=self.colors["topbar"])
        self.topbar_left.pack(side=tk.LEFT, anchor="w")
        self.topbar_right = tk.Frame(self.topbar, bg=self.colors["topbar"])
        self.topbar_right.pack(side=tk.RIGHT, anchor="e")
        self._update_topbar()

    def _update_topbar(self):
        for w in self.topbar_left.winfo_children(): w.destroy()
        for w in self.topbar_right.winfo_children(): w.destroy()

        ttk.Label(self.topbar_left, text="Green+", style="Header.TLabel").pack(side=tk.LEFT, padx=(6,12))
        # search field (visual only) for UX
        search_var = tk.StringVar()
        sv = ttk.Entry(self.topbar_left, textvariable=search_var, width=30)
        sv.pack(side=tk.LEFT, padx=(0,12))
        sv.insert(0, "Pesquisar tarefas, dicas...")

        if self.usuario:
            ttk.Label(self.topbar_right, text=f"👋 {self.usuario['nome']}", font=("Segoe UI", 11), background=self.colors['topbar']).pack(side=tk.LEFT, padx=10)
            try:
                pontos = int(self.usuario["pontos"])
            except:
                pontos = 0
            nivel = self.usuario.get("nivel","Básico")
            ttk.Label(self.topbar_right, text=f"{nivel}  •  {pontos} pts", font=("Segoe UI", 11, "bold"), background=self.colors['topbar']).pack(side=tk.LEFT, padx=10)

            # barra de progresso até o próximo nível
            rem = pontos_para_proximo_nivel(pontos)
            total_to_next = (100 if nivel=="Básico" else (300 if nivel=="Intermediário" else pontos))
            got = (total_to_next - rem) if total_to_next>0 else total_to_next
            pct = min(1.0, got/ (total_to_next if total_to_next>0 else 1))
            pb = ttk.Progressbar(self.topbar_right, length=160, value=pct*100, style="green.Horizontal.TProgressbar")
            pb.pack(side=tk.LEFT, padx=8, pady=12)

    def clear_body(self):
        for w in self.body.winfo_children():
            if w is not self.topbar:
                w.destroy()
        self.topbar.pack(fill=tk.X, padx=20, pady=(12,6))

    # LOGIN / REGISTRO
    def show_login(self):
        self.usuario = None
        self._update_topbar()
        self.clear_body()
        frame = tk.Frame(self.body, bg=self.colors["bg"])
        frame.pack(expand=True, fill=tk.BOTH)

        card = tk.Frame(frame, bg=self.colors["card"], bd=0, relief=tk.RIDGE)
        card.place(relx=0.5, rely=0.42, anchor="c", width=720, height=420)

        ttk.Label(card, text="Acesse o Green+", style="Header.TLabel").pack(pady=(22,6))
        tk.Label(card, text="Entre com seu e-mail e senha", bg=self.colors["card"]).pack()

        inner = tk.Frame(card, bg=self.colors["card"]) 
        inner.pack(padx=28, pady=18, fill=tk.BOTH, expand=True)

        tk.Label(inner, text="Email", bg=self.colors["card"]).grid(row=0, column=0, sticky="w", padx=8, pady=6)
        email_entry = ttk.Entry(inner, width=40); email_entry.grid(row=0, column=1, pady=6, padx=8)

        tk.Label(inner, text="Senha", bg=self.colors["card"]).grid(row=1, column=0, sticky="w", padx=8, pady=6)
        senha_entry = ttk.Entry(inner, width=40, show="•"); senha_entry.grid(row=1, column=1, pady=6, padx=8)

        def try_login():
            e = email_entry.get().strip()
            s = senha_entry.get().strip()
            if not e or not s:
                messagebox.showerror("Erro", "Preencha email e senha")
                return
            users = carregar_usuarios()
            u = users.get(e)
            if not u or u["senha"] != md5(s):
                messagebox.showerror("Erro", "Email ou senha inválidos")
                return
            self.usuario = u
            users[e]["ultimo_login"] = str(datetime.date.today())
            salvar_usuarios_dict(users)
            messagebox.showinfo("Bem-vindo", f"Olá, {u['nome']}! Bem-vindo ao Green+.")
            self._update_topbar()
            self.show_dashboard()

        ttk.Button(inner, text="Entrar", command=try_login, style="Accent.TButton").grid(row=2, column=1, pady=(12,6), sticky="e", padx=8)
        signup_frame = tk.Frame(card, bg=self.colors["card"])
        signup_frame.pack(side=tk.BOTTOM, pady=12)
        tk.Label(signup_frame, text="Ainda não tem conta?", bg=self.colors["card"]).pack(side=tk.LEFT)
        ttk.Button(signup_frame, text="Criar Conta", command=self.show_register).pack(side=tk.LEFT, padx=8)

    def show_register(self):
        self.clear_body()
        frame = tk.Frame(self.body, bg=self.colors["bg"])
        frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=12)

        card = tk.Frame(frame, bg=self.colors["card"]) 
        card.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ttk.Label(card, text="Cadastro - Green+", style="Header.TLabel").pack(pady=(12,6))
        inner = tk.Frame(card, bg=self.colors["card"]) 
        inner.pack(padx=18, pady=12, fill=tk.BOTH, expand=True)

        tk.Label(inner, text="Nome Completo", bg=self.colors["card"]).grid(row=0, column=0, sticky="w", padx=6, pady=6)
        nome_e = ttk.Entry(inner, width=40); nome_e.grid(row=0, column=1, pady=6, padx=6)

        tk.Label(inner, text="Email", bg=self.colors["card"]).grid(row=1, column=0, sticky="w", padx=6, pady=6)
        email_e = ttk.Entry(inner, width=40); email_e.grid(row=1, column=1, pady=6, padx=6)

        tk.Label(inner, text="Senha", bg=self.colors["card"]).grid(row=2, column=0, sticky="w", padx=6, pady=6)
        senha_e = ttk.Entry(inner, width=40, show="•"); senha_e.grid(row=2, column=1, pady=6, padx=6)

        tk.Label(inner, text="Confirmar Senha", bg=self.colors["card"]).grid(row=3, column=0, sticky="w", padx=6, pady=6)
        conf_e = ttk.Entry(inner, width=40, show="•"); conf_e.grid(row=3, column=1, pady=6, padx=6)

        def register_action():
            nome = nome_e.get().strip()
            email = email_e.get().strip()
            senha = senha_e.get().strip()
            conf = conf_e.get().strip()
            if not (nome and email and senha and conf):
                messagebox.showerror("Erro", "Preencha todos os campos.")
                return
            if senha != conf:
                messagebox.showerror("Erro", "As senhas não coincidem.")
                return
            users = carregar_usuarios()
            if email in users:
                messagebox.showerror("Erro", "Este email já está cadastrado.")
                return
            users[email] = {
                "email": email,
                "senha": md5(senha),
                "nome": nome,
                "pontos": "0",
                "nivel": "Básico",
                "ultimo_login": str(datetime.date.today()),
                "badges": "",
                "rewards": ""
            }
            salvar_usuarios_dict(users)
            messagebox.showinfo("Sucesso", "Conta criada! Faça login.")
            self.show_login()

        btns = tk.Frame(card, bg=self.colors["card"])
        btns.pack(pady=8)
        ttk.Button(btns, text="Cadastrar", command=register_action, style="Accent.TButton").pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Voltar", command=self.show_login).pack(side=tk.LEFT, padx=6)

    # 
    # Dashboard 
    def show_dashboard(self):
        if not self._ensure_user(): return
        self.clear_body()
        self._update_topbar()

        container = tk.Frame(self.body, bg=self.colors["bg"]) 
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)

        # Top cards
        top = tk.Frame(container, bg=self.colors["bg"]) 
        top.pack(fill=tk.X)
        def card(parent, title, value, subtitle=""):
            c = tk.Frame(parent, bg=self.colors["card"], bd=0, relief=tk.RIDGE)
            c.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=8)
            ttk.Label(c, text=title, style="CardHeader.TLabel").pack(anchor="w", padx=14, pady=(12,0))
            tk.Label(c, text=value, bg=self.colors["card"], font=("Segoe UI", 18, "bold"), fg=self.colors["primary"]).pack(anchor="w", padx=14, pady=(6,8))
            if subtitle:
                ttk.Label(c, text=subtitle, style="Muted.TLabel").pack(anchor="w", padx=14, pady=(0,12))
            return c

        pontos = int(self.usuario.get("pontos","0"))
        nivel = self.usuario.get("nivel","Básico")
        badges = self.usuario.get("badges","Nenhum")
        card(top, "⭐ Pontuação", f"{pontos} pts", "Acumule pontos realizando tarefas")
        card(top, "🏷 Nível", nivel, "Progresso atual")
        card(top, "🎖️ Badges", badges, "Conquistas desbloqueadas")

        # Middle area: grafico + resumo
        mid = tk.Frame(container, bg=self.colors["bg"]) 
        mid.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        left = tk.Frame(mid, bg=self.colors["bg"]) 
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        right = tk.Frame(mid, bg=self.colors["bg"], width=320)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=8)

        # gráfico 7 dias
        fig = Figure(figsize=(6,3.2), dpi=100)
        ax = fig.add_subplot(111)
        hoje = datetime.date.today()
        days = [(hoje - datetime.timedelta(days=i)) for i in reversed(range(7))]
        labels = [d.strftime("%d %b") for d in days]
        pts_por_dia = {str(d):0 for d in days}
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r["email"] == self.usuario["email"] and r["data"] in pts_por_dia:
                        pts_por_dia[r["data"]] += int(r["pontos"])
        except FileNotFoundError:
            pass
        values = [pts_por_dia[str(d)] for d in days]
        ax.plot(labels, values, marker="o", linewidth=2)
        ax.set_title("Pontos nos últimos 7 dias")
        ax.set_ylabel("Pontos")
        ax.grid(alpha=0.3)
        canvas = FigureCanvasTkAgg(fig, master=left)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Right: quick actions + dica
        quick = tk.Frame(right, bg=self.colors["card"]) 
        quick.pack(fill=tk.BOTH, padx=6, pady=6)
        ttk.Label(quick, text="Ações Rápidas", style="CardHeader.TLabel").pack(anchor="w", padx=12, pady=(8,6))
        ttk.Button(quick, text="Realizar Tarefa", command=self.show_tasks).pack(fill=tk.X, padx=12, pady=6)
        ttk.Button(quick, text="Ver Calendário", command=self.show_calendar).pack(fill=tk.X, padx=12, pady=6)
        ttk.Button(quick, text="Ver Ranking", command=self.show_ranking).pack(fill=tk.X, padx=12, pady=6)

        tip_card = tk.Frame(right, bg=self.colors["card"]) 
        tip_card.pack(fill=tk.BOTH, padx=6, pady=6, expand=True)
        ttk.Label(tip_card, text="Dica Sustentável", style="CardHeader.TLabel").pack(anchor="w", padx=12, pady=(8,4))
        dicas = [
            "Use uma garrafa reutilizável ao invés de descartáveis.",
            "Reduza o tempo do banho para economizar água.",
            "Desligue carregadores da tomada quando não estiverem em uso."
        ]
        tk.Label(tip_card, text=random.choice(dicas), wraplength=260, justify="left", bg=self.colors["card"]).pack(padx=12, pady=8)

    # ---------------- Tasks ----------------
    def show_tasks(self):
        if not self._ensure_user(): return
        self.clear_body()

        frame = tk.Frame(self.body, bg=self.colors["bg"]) 
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)

        ttk.Label(frame, text="Tarefas Disponíveis", style="Header.TLabel").pack(anchor="w", pady=(6,8))

        content = tk.Frame(frame, bg=self.colors["bg"]) 
        content.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(content, bg=self.colors["bg"]) 
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,12))
        right = tk.Frame(content, bg=self.colors["bg"], width=320)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        nivel = self.usuario.get("nivel","Básico")
        tarefas = obter_tarefas_por_nivel(nivel)
        if not tarefas:
            tk.Label(left, text="Nenhuma tarefa disponível para seu nível.", bg=self.colors["bg"]).pack(pady=20)
            return

        for t in tarefas:
            card = tk.Frame(left, bg=self.colors["card"], bd=0, relief=tk.RIDGE)
            card.pack(fill=tk.X, padx=6, pady=10)
            ttk.Label(card, text=t["tarefa"], style="CardHeader.TLabel").pack(anchor="w", padx=12, pady=(8,4))
            tk.Label(card, text=t["descricao"], bg=self.colors["card"], wraplength=720, justify="left").pack(anchor="w", padx=12, pady=(0,8))
            pts = random.randint(int(t["pontos_minimo"]), int(t["pontos_maximo"]))
            tk.Label(card, text=f"Recompensa: {pts} pts", bg=self.colors["card"], font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(0,8))

            rel = scrolledtext.ScrolledText(card, height=4, width=90)
            rel.pack(padx=12, pady=(0,8))

            btnf = tk.Frame(card, bg=self.colors["card"]) 
            btnf.pack(fill=tk.X, padx=12, pady=(0,12))
            def concluir(tarefa=t["tarefa"], pontos=pts, rel_widget=rel):
                texto = rel_widget.get("1.0", tk.END).strip()
                if not texto:
                    messagebox.showerror("Erro", "Escreva um relatório da atividade. (Obrigatório)")
                    return
                if contar_tarefas_dia(self.usuario["email"]) >= 2:
                    messagebox.showwarning("Limite", "Você já completou 2 tarefas hoje.")
                    return
                users = carregar_usuarios()
                u = users[self.usuario["email"]]
                u["pontos"] = str(int(u["pontos"]) + pontos)
                novo_nivel = definir_nivel(int(u["pontos"]))
                if novo_nivel != u["nivel"]:
                    u["nivel"] = novo_nivel
                    adicionar_badge(u, novo_nivel)
                    messagebox.showinfo("Parabéns!", f"Você subiu para o nível {novo_nivel}!")
                salvar_usuarios_dict(users)
                salvar_progresso(self.usuario["email"], tarefa, pontos, texto)
                self.usuario = users[self.usuario["email"]]
                self._update_topbar()
                messagebox.showinfo("Sucesso", f"Tarefa concluída! +{pontos} pts")
                self.show_dashboard()
            ttk.Button(btnf, text="Concluir", command=concluir, style="Accent.TButton").pack(side=tk.LEFT)
            ttk.Button(btnf, text="Cancelar", command=lambda: self.show_dashboard()).pack(side=tk.LEFT, padx=8)

        # Right: instruções e limite diário
        info_card = tk.Frame(right, bg=self.colors["card"]) 
        info_card.pack(fill=tk.BOTH, padx=6, pady=6)
        ttk.Label(info_card, text="Como funciona", style="CardHeader.TLabel").pack(anchor="w", padx=12, pady=(8,6))
        tk.Label(info_card, text="1) Escolha uma tarefa.\n2) Escreva um breve relatório (obrigatório).\n3) Clique em Concluir para ganhar pontos.", bg=self.colors["card"], justify="left", wraplength=300).pack(padx=12, pady=6)
        tk.Label(info_card, text=f"Limite diário: 2 tarefas (Você já completou {contar_tarefas_dia(self.usuario['email'])})", bg=self.colors["card"], font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=12, pady=(6,12))

    # --------------- Calendar ----------------
    def show_calendar(self):
        if not self._ensure_user(): return
        self.clear_body()
        ttk.Label(self.body, text="Calendário", style="Header.TLabel").pack(anchor="w", padx=20, pady=(12,6))
        frame = tk.Frame(self.body, bg=self.colors["bg"]) 
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=8)

        left = tk.Frame(frame, bg=self.colors["bg"]) 
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,12))
        right = tk.Frame(frame, bg=self.colors["bg"]) 
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cal = Calendar(left, selectmode="day")
        cal.pack(padx=6, pady=6)

        lbl = ttk.Label(right, text="Tarefas no dia selecionado", style="SubHeader.TLabel")
        lbl.pack(anchor="w", padx=6, pady=(6,4))

        listbox = tk.Listbox(right)
        listbox.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        def mostrar():
            sel = cal.get_date()
            for fmt in ("%m/%d/%y", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    d = datetime.datetime.strptime(sel, fmt).date()
                    break
                except Exception:
                    d = None
            if d is None:
                d = datetime.date.today()
            dstr = str(d)
            listbox.delete(0, tk.END)
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        if r["email"] == self.usuario["email"] and r["data"] == dstr:
                            listbox.insert(tk.END, f"{r['tarefa']} (+{r['pontos']} pts) - {r['relatorio'][:80]}...")
            except FileNotFoundError:
                pass

        ttk.Button(left, text="Mostrar tarefas", command=mostrar).pack(pady=6)

    # ------------- Histórico ----------------
    def show_history(self):
        if not self._ensure_user(): return
        self.clear_body()
        ttk.Label(self.body, text="Histórico de Atividades", style="Header.TLabel").pack(anchor="w", padx=20, pady=(12,6))
        frame = tk.Frame(self.body, bg=self.colors["bg"]) 
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=6)
        cols = ("data","tarefa","pontos","relatorio")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c.capitalize())
            tree.column(c, anchor="w", width=150)
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = ttk.Scrollbar(frame, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscroll=scrollbar.set)

        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r["email"] == self.usuario["email"]:
                        tree.insert("", tk.END, values=(r["data"], r["tarefa"], f"+{r['pontos']}", r["relatorio"][:60]+"..."))
        except FileNotFoundError:
            pass

    # -------------- Ranking ----------------
    def show_ranking(self):
        self.clear_body()
        ttk.Label(self.body, text="Ranking - Top 5", style="Header.TLabel").pack(anchor="w", padx=20, pady=(12,6))
        frame = tk.Frame(self.body, bg=self.colors["bg"]) 
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=6)

        users = list(carregar_usuarios().values())
        users_sorted = sorted(users, key=lambda u: int(u["pontos"]), reverse=True)[:5]
        for idx, u in enumerate(users_sorted, start=1):
            bgc = self.colors["card"]
            card = tk.Frame(frame, bg=bgc, bd=0, relief=tk.RIDGE)
            card.pack(fill=tk.X, padx=6, pady=8)
            medal = "🥇" if idx==1 else ("🥈" if idx==2 else ("🥉" if idx==3 else f"#{idx}"))
            ttk.Label(card, text=f"{medal}  {u['nome']}", style="CardHeader.TLabel").pack(anchor="w", padx=12, pady=(8,0))
            tk.Label(card, text=f"Pontos: {u['pontos']}  •  Nível: {u['nivel']}", bg=bgc).pack(anchor="w", padx=12, pady=(0,8))

        def ver_completo():
            top = tk.Toplevel(self.root)
            top.title("Ranking Completo")
            top.geometry("700x450")
            tree = ttk.Treeview(top, columns=("nome","pontos","nivel"), show="headings")
            tree.heading("nome", text="Nome")
            tree.heading("pontos", text="Pontos")
            tree.heading("nivel", text="Nível")
            tree.pack(fill=tk.BOTH, expand=True)
            for u in sorted(users, key=lambda x: int(x["pontos"]), reverse=True):
                tree.insert("", tk.END, values=(u["nome"], u["pontos"], u["nivel"]))
        ttk.Button(frame, text="Ver ranking completo", command=ver_completo).pack(pady=10)

    # -------------- Achievements / Conquistas ----------------
    def show_achievements(self):
        """
        Exibe as conquistas (badges) do usuário e lista global de recompensas disponiveis,
        mostrando quais podem ser resgatadas. Esta tela mostra tanto as badges (nível)
        quanto o catálogo de recompensas (resgatar).
        """
        if not self._ensure_user(): return
        self.clear_body()
        ttk.Label(self.body, text="Conquistas e Recompensas", style="Header.TLabel").pack(anchor="w", padx=20, pady=(12,6))
        frame = tk.Frame(self.body, bg=self.colors["bg"]) 
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=6)

        top = tk.Frame(frame, bg=self.colors["bg"]) 
        top.pack(fill=tk.X, pady=(0,8))
        ttk.Label(top, text="Suas Badges", style="SubHeader.TLabel").pack(anchor="w")
        badges_text = self.usuario.get("badges","")
        bframe = tk.Frame(top, bg=self.colors["bg"]) 
        bframe.pack(fill=tk.X, pady=(6,8))
        if not badges_text:
            tk.Label(bframe, text="Nenhuma conquista ainda. Realize tarefas para ganhar badges!", bg=self.colors["bg"]).pack(pady=4)
        else:
            for b in badges_text.split(","):
                lbl = tk.Label(bframe, text=b.strip(), bg=self.colors["card"], font=("Segoe UI", 11), bd=0, relief=tk.RIDGE, padx=8, pady=6)
                lbl.pack(side=tk.LEFT, padx=6)

        # Recompensas disponíveis (catálogo público)
        ttk.Label(frame, text="Catálogo de Recompensas (visível a todos)", style="SubHeader.TLabel").pack(anchor="w", pady=(8,6))
        catalog = tk.Frame(frame, bg=self.colors["bg"]) 
        catalog.pack(fill=tk.BOTH, expand=True)

        rewards = carregar_recompensas()
        nivel_ord = {"Básico":0, "Intermediário":1, "Avançado":2}
        rewards_sorted = sorted(rewards, key=lambda r: (nivel_ord.get(r["nivel"],0), r["custo_pontos"]))

        for r in rewards_sorted:
            card = tk.Frame(catalog, bg=self.colors["card"], bd=0, relief=tk.RIDGE)
            card.pack(fill=tk.X, padx=6, pady=8)
            left = tk.Frame(card, bg=self.colors["card"]) 
            left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
            right = tk.Frame(card, bg=self.colors["card"]) 
            right.pack(side=tk.RIGHT, padx=8, pady=8)

            ttk.Label(left, text=f"{r['titulo']}  ({r['nivel']})", style="CardHeader.TLabel").pack(anchor="w")
            tk.Label(left, text=f"{r['descricao']}", bg=self.colors["card"], wraplength=720, justify="left").pack(anchor="w", pady=(4,6))
            tk.Label(left, text=f"Custo: {r['custo_pontos']} pts", bg=self.colors["card"], font=("Segoe UI", 10, "bold")).pack(anchor="w")

            u = self.usuario
            user_pontos = int(u.get("pontos","0"))
            user_nivel = u.get("nivel","Básico")
            niveis_ordem = {"Básico": 0, "Intermediário": 1, "Avançado": 2}
            nivel_req_ok = niveis_ordem.get(user_nivel,0) >= niveis_ordem.get(r["nivel"],0)
            ja_resgatada = usuario_tem_resgatado(u, r["id"])
            if ja_resgatada:
                ttk.Label(right, text="✔️ Resgatada", style="CardHeader.TLabel").pack(anchor="e")
                tk.Label(right, text=f"Resgatada", bg=self.colors["card"]).pack(anchor="e")
            else:
                if nivel_req_ok:
                    if user_pontos >= r["custo_pontos"]:
                        ttk.Button(right, text="Resgatar", command=lambda rid=r["id"]: self._handle_resgatar(rid)).pack(anchor="e", pady=6)
                        tk.Label(right, text="Disponível", bg=self.colors["card"]).pack(anchor="e")
                    else:
                        tk.Label(right, text=f"Bloqueado — faltam {r['custo_pontos'] - user_pontos} pts", bg=self.colors["card"], fg=self.colors["muted"]).pack(anchor="e")
                else:
                    tk.Label(right, text=f"🔒 Requer nível {r['nivel']}", bg=self.colors["card"], fg=self.colors["muted"]).pack(anchor="e")

        ttk.Label(frame, text="Recompensas que você resgatou", style="SubHeader.TLabel").pack(anchor="w", pady=(12,4))
        rframe = tk.Frame(frame, bg=self.colors["bg"]) 
        rframe.pack(fill=tk.X, pady=(0,12))
        claimed = self.usuario.get("rewards","")
        if not claimed:
            tk.Label(rframe, text="Nenhuma recompensa resgatada ainda.", bg=self.colors["bg"]).pack(anchor="w")
        else:
            ids = [i for i in claimed.split(";") if i]
            for rid in ids:
                rec = obter_recompensa_por_id(rid)
                if rec:
                    tk.Label(rframe, text=f"• {rec['titulo']} ({rec['nivel']})", bg=self.colors["bg"]).pack(anchor="w")

    def _handle_resgatar(self, reward_id):
        ok, msg = resgatar_recompensa_para_usuario(self.usuario["email"], reward_id)
        if ok:
            users = carregar_usuarios()
            self.usuario = users[self.usuario["email"]]
            salvar_usuarios_dict(users)
            self._update_topbar()
            messagebox.showinfo("Resgate", msg)
            self.show_achievements()
        else:
            messagebox.showerror("Resgate", msg)

    # Tela que mostra catálogo público (sem ações de resgate) - útil para visualização geral
    def show_rewards_public(self):
        if not self._ensure_user(): return
        self.clear_body()
        ttk.Label(self.body, text="Catálogo de Recompensas (Público)", style="Header.TLabel").pack(anchor="w", padx=20, pady=(12,6))
        frame = tk.Frame(self.body, bg=self.colors["bg"]) 
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=6)

        rewards = carregar_recompensas()
        nivel_ord = {"Básico":0, "Intermediário":1, "Avançado":2}
        for r in sorted(rewards, key=lambda r: (nivel_ord.get(r["nivel"],0), r["custo_pontos"])):
            card = tk.Frame(frame, bg=self.colors["card"], bd=0, relief=tk.RIDGE)
            card.pack(fill=tk.X, padx=6, pady=8)
            ttk.Label(card, text=f"{r['titulo']}  ({r['nivel']}) - {r['custo_pontos']} pts", style="CardHeader.TLabel").pack(anchor="w", padx=12, pady=8)
            tk.Label(card, text=r["descricao"], bg=self.colors["card"], wraplength=900, justify="left").pack(anchor="w", padx=12, pady=(0,8))

    # -------------- Perfil ----------------
    def show_profile(self):
        if not self._ensure_user(): return
        self.clear_body()
        ttk.Label(self.body, text="Perfil", style="Header.TLabel").pack(anchor="w", padx=20, pady=(12,6))
        frame = tk.Frame(self.body, bg=self.colors["bg"]) 
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=6)
        card = tk.Frame(frame, bg=self.colors["card"]) 
        card.pack(fill=tk.X, padx=6, pady=6)

        tk.Label(card, text=f"Nome: {self.usuario['nome']}", bg=self.colors["card"], font=("Segoe UI", 12)).pack(anchor="w", padx=12, pady=(10,4))
        tk.Label(card, text=f"Email: {self.usuario['email']}", bg=self.colors["card"], font=("Segoe UI", 11)).pack(anchor="w", padx=12, pady=(0,6))
        tk.Label(card, text=f"Nível: {self.usuario['nivel']}  •  Pontos: {self.usuario['pontos']}", bg=self.colors["card"], font=("Segoe UI", 11)).pack(anchor="w", padx=12, pady=(0,6))

        tk.Label(card, text=f"Badges: {self.usuario.get('badges','Nenhuma')}", bg=self.colors["card"], font=("Segoe UI", 11)).pack(anchor="w", padx=12, pady=(0,6))
        tk.Label(card, text=f"Recompensas resgatadas: {self.usuario.get('rewards','Nenhuma')}", bg=self.colors["card"], font=("Segoe UI", 10)).pack(anchor="w", padx=12, pady=(0,10))

        def alterar_senha():
            top = tk.Toplevel(self.root)
            top.title("Alterar Senha")
            tk.Label(top, text="Senha atual").grid(row=0, column=0, padx=8, pady=6)
            s_atual = ttk.Entry(top, show="•"); s_atual.grid(row=0, column=1, padx=8, pady=6)
            tk.Label(top, text="Nova senha").grid(row=1, column=0, padx=8, pady=6)
            s_nova = ttk.Entry(top, show="•"); s_nova.grid(row=1, column=1, padx=8, pady=6)
            tk.Label(top, text="Confirmar").grid(row=2, column=0, padx=8, pady=6)
            s_conf = ttk.Entry(top, show="•"); s_conf.grid(row=2, column=1, padx=8, pady=6)
            def salvar():
                atual = s_atual.get().strip()
                nova = s_nova.get().strip()
                conf = s_conf.get().strip()
                users = carregar_usuarios()
                u = users[self.usuario["email"]]
                if md5(atual) != u["senha"]:
                    messagebox.showerror("Erro", "Senha atual incorreta.")
                    return
                if nova != conf:
                    messagebox.showerror("Erro", "As senhas não coincidem.")
                    return
                u["senha"] = md5(nova)
                salvar_usuarios_dict(users)
                messagebox.showinfo("Sucesso", "Senha alterada.")
                top.destroy()
            ttk.Button(top, text="Salvar", command=salvar).grid(row=3, column=1, pady=8)

        ttk.Button(card, text="Alterar Senha", command=alterar_senha).pack(padx=12, pady=10, anchor="w")

    # ------------- Helpers -------------
    def _ensure_user(self):
        if not self.usuario:
            messagebox.showwarning("Atenção", "Faça login para acessar essa área.")
            self.show_login()
            return False
        return True

    def logout(self):
        self.usuario = None
        messagebox.showinfo("Sessão", "Você saiu do sistema.")
        self.show_login()

# -------------- Run app -------------
if __name__ == "__main__":
    root = tk.Tk()
    app = GreenPlusPro(root)
    root.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext




