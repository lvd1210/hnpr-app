import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import random
import secrets

# ==========================================
# 1. PAGE CONFIG & CSS STYLING (HIERARCHY UI)
# ==========================================
st.set_page_config(page_title="HNX Pickleball Allstars", layout="wide", page_icon="🏓")

DB_PATH = "hnx_pickball_allstars.db"

st.markdown("""
<style>
    /* --- Global Font & Colors --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: #1f2937;
    }

    :root {
        --primary-color: #2563EB;
        --bg-light: #F3F4F6;
        --text-gray: #6B7280;
    }

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
    }

    /* ========================================================= */
    /* 🎯 MENU CHÍNH (NAVIGATION BAR) - STYLE "PILLS" */
    /* ========================================================= */
    /* Chúng ta bọc Menu chính trong một div class 'main-menu-tabs' ở hàm main() */
    
    .main-menu-tabs div[data-baseweb="tab-list"] {
        background-color: #f0f2f6 !important; /* Nền xám cho cả thanh menu */
        padding: 4px 4px 0px 4px !important;
        border-radius: 8px 8px 0 0;
        gap: 8px;
    }

    /* Các nút trong menu chính */
    .main-menu-tabs div[data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: #444 !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        margin-bottom: 4px !important;
        border-radius: 6px !important;
        transition: 0.2s;
    }

    /* Khi hover vào menu chính */
    .main-menu-tabs div[data-baseweb="tab"]:hover {
        background-color: #e5e7eb !important;
    }

    /* Mục đang được chọn ở menu chính */
    .main-menu-tabs button[aria-selected="true"] {
        background-color: #ffffff !important; /* Nền trắng nổi bật */
        color: var(--primary-color) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08) !important;
    }


    /* ========================================================= */
    /* 📂 TAB CON (SUB-TABS) - STYLE "CLEAN UNDERLINE" */
    /* ========================================================= */
    /* Áp dụng cho các tab KHÔNG nằm trong .main-menu-tabs */
    
    div[data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 0px;
    }
    
    /* Reset style mặc định để tránh xung đột */
    div[data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #6B7280;
        font-weight: 500;
        font-size: 15px;
        padding-bottom: 10px;
    }
    
    /* Style chọn cho Tab con: Chỉ gạch chân, không đổi nền */
    button[aria-selected="true"] {
        color: var(--primary-color) !important;
        border-bottom: 2px solid var(--primary-color) !important;
        font-weight: 700 !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* ========================================================= */
    /* 🃏 CARD & INFO GRID STYLE */
    /* ========================================================= */
    .tournament-card {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .t-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 12px;
    }

    .info-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        background-color: #F9FAFB;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #f3f4f6;
    }
    .info-item { display: flex; flex-direction: column; }
    .info-label {
        font-size: 0.75rem; 
        color: #6B7280; 
        text-transform: uppercase; 
        font-weight: 600;
        margin-bottom: 4px;
    }
    .info-value {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1F2937;
    }

    /* --- Buttons --- */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        border: 1px solid #d1d5db;
    }
    .stButton > button:hover {
        border-color: var(--primary-color);
        color: var(--primary-color);
    }
</style>
""", unsafe_allow_html=True)

# --- Init Session State ---
if "user" not in st.session_state:
    st.session_state["user"] = None
if "login_token" not in st.session_state:
    st.session_state["login_token"] = None
if "tournament_view_mode" not in st.session_state:
    st.session_state["tournament_view_mode"] = "list"
if "selected_tournament_id" not in st.session_state:
    st.session_state["selected_tournament_id"] = None
if "editing_tournament_id" not in st.session_state:
    st.session_state["editing_tournament_id"] = None
if "show_create_t" not in st.session_state:
    st.session_state["show_create_t"] = False

# ------------------ DB helpers ------------------ #

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Tables creation (kept same as logic)
    cur.execute("""CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id INTEGER NOT NULL, created_at TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, full_name TEXT NOT NULL, age INTEGER, role TEXT NOT NULL DEFAULT 'player', is_approved INTEGER NOT NULL DEFAULT 0, is_btc INTEGER NOT NULL DEFAULT 0, is_admin INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS tournaments (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, start_date TEXT, end_date TEXT, location TEXT, num_courts INTEGER, is_active INTEGER NOT NULL DEFAULT 0)""")
    
    cur.execute("PRAGMA table_info(tournaments)")
    cols = [r[1] for r in cur.fetchall()]
    if "competition_type" not in cols: cur.execute("ALTER TABLE tournaments ADD COLUMN competition_type TEXT")
    if "use_pools" not in cols: cur.execute("ALTER TABLE tournaments ADD COLUMN use_pools INTEGER NOT NULL DEFAULT 1")
    if "adv_per_pool" not in cols: cur.execute("ALTER TABLE tournaments ADD COLUMN adv_per_pool INTEGER")

    cur.execute("""CREATE TABLE IF NOT EXISTS tournament_players (tournament_id INTEGER NOT NULL, user_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'approved', group_name TEXT, PRIMARY KEY (tournament_id, user_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS personal_ranking_items (owner_id INTEGER NOT NULL, ranked_user_id INTEGER NOT NULL, position INTEGER NOT NULL, PRIMARY KEY (owner_id, ranked_user_id))""")
    # BXH chính thức do Ban tổ chức thiết lập
    cur.execute("""
        CREATE TABLE IF NOT EXISTS btc_ranking_items (
            ranked_user_id INTEGER PRIMARY KEY,
            position      INTEGER NOT NULL
        )
    """)
    
    cur.execute("""CREATE TABLE IF NOT EXISTS competitors (id INTEGER PRIMARY KEY AUTOINCREMENT, tournament_id INTEGER NOT NULL, name TEXT NOT NULL, kind TEXT NOT NULL, pool_name TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS competitor_members (competitor_id INTEGER NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY (competitor_id, user_id))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, tournament_id INTEGER NOT NULL, competitor1_id INTEGER NOT NULL, competitor2_id INTEGER NOT NULL, score1 INTEGER NOT NULL, score2 INTEGER NOT NULL, winner_id INTEGER NOT NULL, reported_by INTEGER, confirmed_by INTEGER)""")

    cur.execute("PRAGMA table_info(matches)")
    mcols = [r[1] for r in cur.fetchall()]
    if "team1_p1_id" not in mcols: cur.execute("ALTER TABLE matches ADD COLUMN team1_p1_id INTEGER")
    if "team1_p2_id" not in mcols: cur.execute("ALTER TABLE matches ADD COLUMN team1_p2_id INTEGER")
    if "team2_p1_id" not in mcols: cur.execute("ALTER TABLE matches ADD COLUMN team2_p1_id INTEGER")
    if "team2_p2_id" not in mcols: cur.execute("ALTER TABLE matches ADD COLUMN team2_p2_id INTEGER")

    conn.commit()
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        password_hash = hash_password("admin")
        cur.execute("INSERT INTO users (username, password_hash, full_name, age, role, is_approved, is_btc, is_admin, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", ("admin", password_hash, "Administrator", 0, "admin", 1, 1, 1, datetime.utcnow().isoformat()))
        conn.commit()
    conn.close()

# ------------------ Auth helpers ------------------ #

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def verify_password(pw: str, pw_hash: str) -> bool:
    return hash_password(pw) == pw_hash

def get_user_by_username(username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row

def get_user_by_id(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def login(username, password):
    user = get_user_by_username(username)
    if not user: return None, "Không tìm thấy tài khoản"
    if not verify_password(password, user["password_hash"]): return None, "Sai mật khẩu"
    if not user["is_approved"]: return None, "Tài khoản chưa được phê duyệt"
    return user, None

# ------------------ Session helpers ------------------ #

def create_session_token(user_id: int) -> str:
    token = secrets.token_hex(16)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)", (token, user_id, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return token

def get_user_by_session_token(token: str):
    if not token: return None
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?", (token,))
        row = cur.fetchone()
    except sqlite3.OperationalError: row = None
    conn.close()
    return row

def delete_session_token(token: str):
    if not token: return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def require_login():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.warning("⚠️ Bạn cần đăng nhập để sử dụng chức năng này.")
        st.stop()

def require_role(roles):
    require_login()
    u = st.session_state["user"]
    is_admin = bool(u.get("is_admin", 0))
    is_btc = bool(u.get("is_btc", 0))
    ok = False
    if "admin" in roles and is_admin: ok = True
    if "btc" in roles and (is_btc or is_admin): ok = True
    if "player" in roles: ok = True
    if not ok:
        st.error("⛔ Bạn không có quyền truy cập.")
        st.stop()

# ------------------ Logic & Data Access ------------------ #

def get_all_players(only_approved=True):
    conn = get_conn()
    cur = conn.cursor()
    if only_approved: cur.execute("SELECT * FROM users WHERE role = 'player' AND is_approved = 1 ORDER BY full_name")
    else: cur.execute("SELECT * FROM users ORDER BY full_name")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_personal_ranking(owner_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT pri.ranked_user_id, pri.position, u.full_name FROM personal_ranking_items pri JOIN users u ON u.id = pri.ranked_user_id WHERE pri.owner_id = ? ORDER BY pri.position ASC", (owner_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def save_personal_ranking(owner_id, ordered_ids):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM personal_ranking_items WHERE owner_id = ?", (owner_id,))
    for pos, uid in enumerate(ordered_ids, start=1):
        cur.execute("INSERT INTO personal_ranking_items (owner_id, ranked_user_id, position) VALUES (?, ?, ?)", (owner_id, uid, pos))
    conn.commit()
    conn.close()

def delete_personal_ranking(owner_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM personal_ranking_items WHERE owner_id = ?", (owner_id,))
    conn.commit()
    conn.close()

def compute_hnpr():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT ranked_user_id, AVG(position) AS avg_pos, COUNT(DISTINCT owner_id) AS vote_count FROM personal_ranking_items GROUP BY ranked_user_id HAVING vote_count > 0 ORDER BY avg_pos ASC")
    rows = cur.fetchall()
    result = []
    rank = 1
    for r in rows:
        user = get_user_by_id(r["ranked_user_id"])
        if not user: continue
        result.append({"rank": rank, "user_id": r["ranked_user_id"], "full_name": user["full_name"], "avg_pos": r["avg_pos"], "vote_count": r["vote_count"]})
        rank += 1
    conn.close()
    return result

def get_hnpr_order_or_alpha():
    ranking = compute_hnpr()
    if ranking: return [r["user_id"] for r in ranking]
    else: return [p["id"] for p in get_all_players(only_approved=True)]

def get_btc_ranking():
    """
    Lấy BXH do Ban tổ chức thiết lập:
    trả về danh sách (ranked_user_id, position, full_name) sắp xếp theo position.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.ranked_user_id, b.position, u.full_name
        FROM btc_ranking_items b
        JOIN users u ON u.id = b.ranked_user_id
        ORDER BY b.position ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def save_btc_ranking(ordered_ids):
    """
    Ghi lại BXH BTC theo thứ tự trong ordered_ids (1 là cao nhất).
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM btc_ranking_items")
    for pos, uid in enumerate(ordered_ids, start=1):
        cur.execute("""
            INSERT INTO btc_ranking_items (ranked_user_id, position)
            VALUES (?, ?)
        """, (uid, pos))
    conn.commit()
    conn.close()

def delete_btc_ranking():
    """
    Xoá toàn bộ BXH BTC.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM btc_ranking_items")
    conn.commit()
    conn.close()

def build_competitor_display_name(comp_id, members_map):
    members = members_map.get(comp_id, [])
    member_names = [m[1] for m in members]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, kind FROM competitors WHERE id = ?", (comp_id,))
    row = cur.fetchone()
    conn.close()
    if not row: return " + ".join(member_names) if member_names else str(comp_id)
    base_name = row["name"]
    kind = row["kind"]
    if kind == "team":
        if member_names: return f"{base_name} ({', '.join(member_names)})"
        return base_name
    else:
        if member_names: return " + ".join(member_names)
        return base_name

def get_tournaments():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tournaments ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_active_tournaments():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tournaments WHERE is_active = 1 ORDER BY start_date")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_tournament_by_id(t_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tournaments WHERE id = ?", (t_id,))
    row = cur.fetchone()
    conn.close()
    return row

def upsert_tournament(t_id, name, start_date, end_date, location, num_courts, is_active, competition_type="pair", use_pools=True, adv_per_pool=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(tournaments)")
    cols = [r[1] for r in cur.fetchall()]
    if "competition_type" not in cols: cur.execute("ALTER TABLE tournaments ADD COLUMN competition_type TEXT")
    if "use_pools" not in cols: cur.execute("ALTER TABLE tournaments ADD COLUMN use_pools INTEGER NOT NULL DEFAULT 1")
    if "adv_per_pool" not in cols: cur.execute("ALTER TABLE tournaments ADD COLUMN adv_per_pool INTEGER")

    if t_id is None:
        cur.execute("INSERT INTO tournaments (name, start_date, end_date, location, num_courts, is_active, competition_type, use_pools, adv_per_pool) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (name, start_date, end_date, location, num_courts, 1 if is_active else 0, competition_type, 1 if use_pools else 0, adv_per_pool))
        t_id = cur.lastrowid
    else:
        cur.execute("UPDATE tournaments SET name = ?, start_date = ?, end_date = ?, location = ?, num_courts = ?, is_active = ?, competition_type = ?, use_pools = ?, adv_per_pool = ? WHERE id = ?", (name, start_date, end_date, location, num_courts, 1 if is_active else 0, competition_type, 1 if use_pools else 0, adv_per_pool, t_id))
    conn.commit()
    conn.close()
    return t_id

def delete_tournament(t_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tournament_players WHERE tournament_id = ?", (t_id,))
    cur.execute("DELETE FROM competitor_members WHERE competitor_id IN (SELECT id FROM competitors WHERE tournament_id = ?)", (t_id,))
    cur.execute("DELETE FROM competitors WHERE tournament_id = ?", (t_id,))
    cur.execute("DELETE FROM matches WHERE tournament_id = ?", (t_id,))
    cur.execute("DELETE FROM tournaments WHERE id = ?", (t_id,))
    conn.commit()
    conn.close()

def get_tournament_players(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT tp.tournament_id, tp.user_id, tp.status, tp.group_name, u.full_name FROM tournament_players tp JOIN users u ON u.id = tp.user_id WHERE tp.tournament_id = ? ORDER BY u.full_name", (tournament_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def set_tournament_players(tournament_id, user_ids):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tournament_players WHERE tournament_id = ?", (tournament_id,))
    for uid in user_ids:
        cur.execute("INSERT INTO tournament_players (tournament_id, user_id, status) VALUES (?, ?, 'approved')", (tournament_id, uid))
    conn.commit()
    conn.close()

def get_competitors(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM competitors WHERE tournament_id = ? ORDER BY id", (tournament_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def clear_competitors_and_matches(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM competitors WHERE tournament_id = ?", (tournament_id,))
    comp_ids = [r["id"] for r in cur.fetchall()]
    if comp_ids: cur.executemany("DELETE FROM competitor_members WHERE competitor_id = ?", [(cid,) for cid in comp_ids])
    cur.execute("DELETE FROM matches WHERE tournament_id = ?", (tournament_id,))
    cur.execute("DELETE FROM competitors WHERE tournament_id = ?", (tournament_id,))
    conn.commit()
    conn.close()

def create_competitor(conn, tournament_id, member_ids):
    cur = conn.cursor()
    placeholders = ",".join("?" * len(member_ids))
    cur.execute(f"SELECT full_name FROM users WHERE id IN ({placeholders}) ORDER BY full_name", member_ids)
    names = [r[0] for r in cur.fetchall()]
    display_name = " + ".join(names)
    kind = "pair" if len(member_ids) == 2 else "team"
    cur.execute("INSERT INTO competitors (tournament_id, name, kind) VALUES (?, ?, ?)", (tournament_id, display_name, kind))
    comp_id = cur.lastrowid
    for uid in member_ids:
        cur.execute("INSERT INTO competitor_members (competitor_id, user_id) VALUES (?, ?)", (comp_id, uid))
    return comp_id

def get_competitor_members_map(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT c.id AS competitor_id, u.id AS user_id, u.full_name FROM competitors c JOIN competitor_members cm ON cm.competitor_id = c.id JOIN users u ON u.id = cm.user_id WHERE c.tournament_id = ? ORDER BY c.id, u.full_name", (tournament_id,))
    rows = cur.fetchall()
    conn.close()
    comp_members = {}
    for r in rows:
        comp_members.setdefault(r["competitor_id"], []).append((r["user_id"], r["full_name"]))
    return comp_members

def get_matches(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT m.*, c1.name AS name1, c2.name AS name2 FROM matches m JOIN competitors c1 ON c1.id = m.competitor1_id JOIN competitors c2 ON c2.id = m.competitor2_id WHERE m.tournament_id = ? ORDER BY m.id", (tournament_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_match(tournament_id, comp1_id, comp2_id, score1, score2, reporter_id, auto_confirm=True, team_players=None):
    if score1 == score2:
        st.warning("Hệ thống chưa hỗ trợ hoà.")
        return
    winner_id = comp1_id if score1 > score2 else comp2_id
    t1_p1, t1_p2, t2_p1, t2_p2 = team_players if team_players else (None, None, None, None)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO matches (tournament_id, competitor1_id, competitor2_id, score1, score2, winner_id, reported_by, confirmed_by, team1_p1_id, team1_p2_id, team2_p1_id, team2_p2_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (tournament_id, comp1_id, comp2_id, score1, score2, winner_id, reporter_id, reporter_id if auto_confirm else None, t1_p1, t1_p2, t2_p1, t2_p2))
    conn.commit()
    conn.close()

def compute_standings(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT c.id, c.name FROM competitors c WHERE c.tournament_id = ?", (tournament_id,))
    competitors = {r["id"]: {"name": r["name"], "wins": 0, "pts_for": 0, "pts_against": 0} for r in cur.fetchall()}
    cur.execute("SELECT * FROM matches WHERE tournament_id = ? AND confirmed_by IS NOT NULL", (tournament_id,))
    for m in cur.fetchall():
        c1 = m["competitor1_id"]; c2 = m["competitor2_id"]; s1 = m["score1"]; s2 = m["score2"]
        competitors[c1]["pts_for"] += s1; competitors[c1]["pts_against"] += s2
        competitors[c2]["pts_for"] += s2; competitors[c2]["pts_against"] += s1
        if m["winner_id"] == c1: competitors[c1]["wins"] += 1
        elif m["winner_id"] == c2: competitors[c2]["wins"] += 1
    conn.close()
    table = []
    for cid, info in competitors.items():
        table.append({"id": cid, "name": info["name"], "wins": info["wins"], "pts_for": info["pts_for"], "pts_against": info["pts_against"], "diff": info["pts_for"] - info["pts_against"]})
    table.sort(key=lambda x: (-x["wins"], -x["diff"], x["name"]))
    return table

def compute_pool_standings(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, pool_name FROM competitors WHERE tournament_id = ? AND pool_name IS NOT NULL", (tournament_id,))
    comps = cur.fetchall()
    if not comps: conn.close(); return {}
    pool_map = {}
    for c in comps:
        pool = c["pool_name"]
        pool_map.setdefault(pool, {})
        pool_map[pool][c["id"]] = {"id": c["id"], "name": c["name"], "wins": 0, "pts_for": 0, "pts_against": 0, "diff": 0}
    cur.execute("SELECT * FROM matches WHERE tournament_id = ? AND confirmed_by IS NOT NULL", (tournament_id,))
    matches = cur.fetchall()
    for m in matches:
        c1 = m["competitor1_id"]; c2 = m["competitor2_id"]; s1 = m["score1"]; s2 = m["score2"]
        for pool, comp_dict in pool_map.items():
            if c1 in comp_dict and c2 in comp_dict:
                comp_dict[c1]["pts_for"] += s1; comp_dict[c1]["pts_against"] += s2
                comp_dict[c2]["pts_for"] += s2; comp_dict[c2]["pts_against"] += s1
                if m["winner_id"] == c1: comp_dict[c1]["wins"] += 1
                elif m["winner_id"] == c2: comp_dict[c2]["wins"] += 1
                break
    conn.close()
    result = {}
    for pool, comp_dict in pool_map.items():
        lst = []
        for cid, info in comp_dict.items():
            info["diff"] = info["pts_for"] - info["pts_against"]
            lst.append(info)
        lst.sort(key=lambda x: (-x["wins"], -x["diff"], x["name"]))
        result[pool] = lst
    return result

# ------------------ UI sections ------------------ #

def ui_login_register():
    st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>Đăng nhập / Đăng ký</h3>", unsafe_allow_html=True)
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        tab_login, tab_register = st.tabs(["Đăng nhập", "Đăng ký"])
        with tab_login:
            st.write(" ")
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            if st.button("Đăng nhập", type="primary", use_container_width=True):
                user, err = login(username, password)
                if err: st.error(err)
                else:
                    token = create_session_token(user["id"])
                    st.session_state["user"] = dict(user)
                    st.session_state["login_token"] = token
                    st.query_params = {"t": token}
                    st.success(f"Xin chào {user['full_name']}!")
                    st.rerun()
        with tab_register:
            st.write(" ")
            full_name = st.text_input("Họ tên")
            age = st.number_input("Tuổi", min_value=5, max_value=100, value=30, step=1)
            username_r = st.text_input("Tên đăng nhập mới")
            password_r = st.text_input("Mật khẩu mới", type="password")
            if st.button("Đăng ký tài khoản mới", use_container_width=True):
                if not (full_name and username_r and password_r): st.warning("Nhập đủ thông tin")
                else:
                    conn = get_conn(); cur = conn.cursor()
                    try:
                        cur.execute("INSERT INTO users (username, password_hash, full_name, age, role, is_approved, created_at) VALUES (?, ?, ?, ?, 'player', 0, ?)", (username_r, hash_password(password_r), full_name, age, datetime.utcnow().isoformat()))
                        conn.commit(); st.success("Đăng ký thành công, chờ duyệt.")
                    except sqlite3.IntegrityError: st.error("Username đã tồn tại.")
                    finally: conn.close()

def ui_member_management():
    require_role(["admin", "btc"])
    st.subheader("👥 Quản lý thành viên")

    # =========================
    # 1. FORM THÊM THÀNH VIÊN MỚI
    # =========================
    with st.expander("➕ Thêm thành viên mới", expanded=True):
        with st.form("add_member_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name_new = st.text_input("Họ tên", key="add_full_name")
                age_new = st.number_input(
                    "Tuổi",
                    min_value=5,
                    max_value=100,
                    value=30,
                    step=1,
                    key="add_age",
                )
            with col2:
                username_new = st.text_input("Username đăng nhập", key="add_username")
                password_new = st.text_input(
                    "Mật khẩu", type="password", key="add_password"
                )

            col_role1, col_role2, col_role3 = st.columns(3)
            with col_role1:
                is_btc_new = st.checkbox("Thuộc Ban tổ chức", key="add_is_btc")
            with col_role2:
                is_admin_new = st.checkbox("Admin", key="add_is_admin")
            with col_role3:
                auto_approve_new = st.checkbox(
                    "Duyệt luôn", value=True, key="add_approve"
                )

            submitted_add = st.form_submit_button("💾 Lưu thành viên mới", type="primary")

            if submitted_add:
                if not (full_name_new and username_new and password_new):
                    st.warning("Vui lòng nhập đủ Họ tên, Username và Mật khẩu.")
                else:
                    role_new = "admin" if is_admin_new else ("btc" if is_btc_new else "player")
                    is_approved_val = 1 if auto_approve_new else 0
                    try:
                        conn_add = get_conn()
                        cur_add = conn_add.cursor()
                        cur_add.execute(
                            """
                            INSERT INTO users (
                                username, password_hash, full_name, age,
                                role, is_approved, is_btc, is_admin, created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                username_new,
                                hash_password(password_new),
                                full_name_new,
                                age_new,
                                role_new,
                                is_approved_val,
                                1 if is_btc_new else 0,
                                1 if is_admin_new else 0,
                                datetime.utcnow().isoformat(),
                            ),
                        )
                        conn_add.commit()
                        conn_add.close()
                        st.success("Đã thêm thành viên mới.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username đã tồn tại, hãy chọn username khác.")

    # =========================
    # 2. DANH SÁCH THÀNH VIÊN & PHÂN QUYỀN
    # =========================
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, full_name, age, role, is_approved, is_btc, is_admin "
        "FROM users ORDER BY created_at DESC"
    )
    users = cur.fetchall()

    if not users:
        st.info("Chưa có thành viên nào.")
        conn.close()
        return

    st.markdown("### Danh sách thành viên")

    with st.form("members_form"):
        header_cols = st.columns([0.05, 0.2, 0.25, 0.1, 0.15, 0.15, 0.1])
        with header_cols[0]:
            st.markdown("**ID**")
        with header_cols[1]:
            st.markdown("**Username**")
        with header_cols[2]:
            st.markdown("**Họ tên**")
        with header_cols[3]:
            st.markdown("**Tuổi**")
        with header_cols[4]:
            st.markdown("**BTC**")
        with header_cols[5]:
            st.markdown("**Admin**")
        with header_cols[6]:
            st.markdown("**Duyệt**")

        st.markdown("---")

        new_is_btc = {}
        new_is_admin = {}
        approve_flags = {}

        for u in users:
            uid = u["id"]
            username = u["username"]
            full_name = u["full_name"]
            age = u["age"]
            is_approved = u["is_approved"]
            is_btc = u["is_btc"]
            is_admin = u["is_admin"]

            cols = st.columns([0.05, 0.2, 0.25, 0.1, 0.15, 0.15, 0.1])
            cols[0].write(uid)
            cols[1].write(username)
            cols[2].write(full_name)
            cols[3].write(age if age is not None else "")

            btc_checked = cols[4].checkbox(
                "BTC",
                value=bool(is_btc),
                key=f"btc_{uid}",
                label_visibility="collapsed",
            )
            admin_checked = cols[5].checkbox(
                "Admin",
                value=bool(is_admin),
                key=f"admin_{uid}",
                label_visibility="collapsed",
            )

            new_is_btc[uid] = 1 if btc_checked else 0
            new_is_admin[uid] = 1 if admin_checked else 0

            if not is_approved:
                approve_checked = cols[6].checkbox(
                    "Approve",
                    key=f"approve_{uid}",
                    label_visibility="collapsed",
                )
                approve_flags[uid] = approve_checked
            else:
                cols[6].markdown("✅")

        st.markdown("---")

        if st.form_submit_button("💾 Lưu cập nhật", type="primary"):
            for u in users:
                uid = u["id"]
                old_btc = u["is_btc"]
                old_admin = u["is_admin"]
                old_approved = u["is_approved"]

                ni_btc = new_is_btc.get(uid, old_btc)
                ni_admin = new_is_admin.get(uid, old_admin)
                new_approved = 1 if uid in approve_flags and approve_flags[uid] else old_approved

                if ni_admin:
                    new_role = "admin"
                elif ni_btc:
                    new_role = "btc"
                else:
                    new_role = "player"

                if (
                    ni_btc != old_btc
                    or ni_admin != old_admin
                    or new_approved != old_approved
                    or new_role != u["role"]
                ):
                    cur.execute(
                        """
                        UPDATE users
                        SET is_btc = ?, is_admin = ?, is_approved = ?, role = ?
                        WHERE id = ?
                        """,
                        (ni_btc, ni_admin, int(new_approved), new_role, uid),
                    )

            conn.commit()
            conn.close()
            st.success("Đã cập nhật.")
            st.rerun()

    conn.close()

def ui_hnpr_page():
    hnpr = compute_hnpr()
    btc_rank = get_btc_ranking()

    user = st.session_state.get("user")
    is_admin = bool(user.get("is_admin", 0)) if user else False
    is_btc = bool(user.get("is_btc", 0)) if user else False
    can_edit_btc = (is_admin or is_btc)

    # =========================
    # PHẦN XEM: HNPR & BXH BTC SIDE-BY-SIDE
    # =========================
    col_left, col_right = st.columns(2)

    # --- Cột trái: HNPR ---
    with col_left:
        st.markdown("#### HNPR (bởi cộng đồng thành viên)")

        if not hnpr:
            st.info("Chưa có đủ dữ liệu để tính HNPR.")
        else:
            display_rows = []
            for idx, r in enumerate(hnpr, start=1):
                medal = ""#🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else ""
                display_rows.append({
                    "STT": f"{idx} {medal}",
                    "Tên VĐV": r["full_name"],
                    "HNPR": round(r["avg_pos"], 2),
                })

            st.dataframe(
                display_rows,
                hide_index=True,
                use_container_width=True,
                height=500,
            )

    # --- Cột phải: BXH BTC ---
    with col_right:
        st.markdown("#### BXH với Ban tổ chức")

        if not btc_rank:
            st.info("Chưa có BXH do Ban tổ chức thiết lập.")
        else:
            btc_rows = []
            for idx, r in enumerate(btc_rank, start=1):
                btc_rows.append({
                    "STT": idx,
                    "Tên VĐV": r["full_name"],
                })

            st.dataframe(
                btc_rows,
                hide_index=True,
                use_container_width=True,
                height=500,
            )

    # =========================
    # PHẦN QUẢN LÝ BXH BTC (chỉ Admin/BTC)
    # =========================
    if not can_edit_btc:
        # Public / player: chỉ xem 2 bảng ở trên
        return

    st.markdown("---")
    st.markdown("### 🛠️ Quản lý BXH do Ban tổ chức thiết lập")

    players = get_all_players(only_approved=True)
    if not players:
        st.info("Chưa có thành viên nào để xếp hạng.")
        return

    # Nếu chưa có BXH BTC: cho phép khởi tạo
    if not btc_rank:
        st.write("Hiện chưa có BXH BTC. Bạn có thể khởi tạo dựa trên HNPR (nếu có) hoặc thứ tự ABC.")

        if st.button("Tạo BXH BTC dựa trên HNPR / ABC", type="primary"):
            if hnpr:
                order_ids = [r["user_id"] for r in hnpr]
                current_set = set(order_ids)
                others = [p for p in players if p["id"] not in current_set]
                others_sorted = sorted(others, key=lambda p: p["full_name"])
                order_ids.extend([p["id"] for p in others_sorted])
            else:
                players_sorted = sorted(players, key=lambda p: p["full_name"])
                order_ids = [p["id"] for p in players_sorted]

            save_btc_ranking(order_ids)
            st.success("Đã khởi tạo BXH BTC.")
            st.rerun()
        return

    # Đã có BXH BTC: UI chỉnh sửa bằng nút lên/xuống
    st.write("Dùng nút lên/xuống để điều chỉnh BXH chung (1 là cao nhất).")

    # Khởi tạo state lần đầu
    if "btc_order" not in st.session_state:
        base_ids = [r["ranked_user_id"] for r in btc_rank]
        base_set = set(base_ids)
        extra_ids = [p["id"] for p in players if p["id"] not in base_set]
        st.session_state["btc_order"] = base_ids + extra_ids

    order = st.session_state["btc_order"]
    id_to_player = {p["id"]: p for p in players}

    for i, uid in enumerate(order):
        player = id_to_player.get(uid)
        if not player:
            continue

        cols = st.columns([0.1, 0.6, 0.15, 0.15])
        cols[0].write(i + 1)
        cols[1].write(player["full_name"])

        up_key = f"btc_up_{uid}_{i}"
        down_key = f"btc_down_{uid}_{i}"

        if cols[2].button("⬆", key=up_key) and i > 0:
            order[i - 1], order[i] = order[i], order[i - 1]
            st.session_state["btc_order"] = order
            st.rerun()

        if cols[3].button("⬇", key=down_key) and i < len(order) - 1:
            order[i + 1], order[i] = order[i], order[i + 1]
            st.session_state["btc_order"] = order
            st.rerun()

    col_save, col_del = st.columns(2)
    with col_save:
        if st.button("💾 Lưu BXH BTC", type="primary", use_container_width=True):
            save_btc_ranking(order)
            st.success("Đã lưu BXH BTC.")

    with col_del:
        if st.button("🗑 Xoá toàn bộ BXH BTC", use_container_width=True):
            delete_btc_ranking()
            st.session_state.pop("btc_order", None)
            st.success("Đã xoá BXH BTC.")
            st.rerun()

def ui_home():
    st.subheader("Các giải đang diễn ra 🔥")
    active_ts = get_active_tournaments()
    if not active_ts: st.info("Chưa có giải đấu nào."); return
    for t in active_ts:
        with st.container():
            st.markdown(f"""
            <div class="tournament-card">
                <div class="t-title">{t['name']}</div>
            """, unsafe_allow_html=True)
            ctype = t["competition_type"] if "competition_type" in t.keys() and t["competition_type"] in ("pair", "team") else "pair"
            use_pools = bool(t["use_pools"]) if "use_pools" in t.keys() else False
            st.markdown(f"""
            <div class="info-grid">
                <div class="info-item"><span class="info-label">📍 Địa điểm</span><span class="info-value">{t['location'] or 'N/A'}</span></div>
                <div class="info-item"><span class="info-label">🗓️ Thời gian</span><span class="info-value">{t['start_date']} - {t['end_date']}</span></div>
                <div class="info-item"><span class="info-label">🎾 Thể loại</span><span class="info-value">{'Theo cặp' if ctype == 'pair' else 'Theo đội'}</span></div>
                <div class="info-item"><span class="info-label">📊 Phân bảng</span><span class="info-value">{'Có' if use_pools else 'Không'}</span></div>
            </div></div>
            """, unsafe_allow_html=True)
            st.write("")
            pair_team_label = "Chia cặp" if ctype == "pair" else "Chia đội"
            tabs_list = ["Thành viên", "Phân nhóm", pair_team_label, "Phân bảng", "Lịch & Kết quả", "Xếp hạng"] if use_pools else ["Thành viên", "Phân nhóm", pair_team_label, "Lịch & Kết quả", "Xếp hạng"]
            tab_objs = st.tabs(tabs_list)
            with tab_objs[0]: ui_tournament_players_view(t["id"])
            with tab_objs[1]: ui_tournament_groups_view(t["id"])
            with tab_objs[2]: ui_tournament_pairs_teams_view(t["id"])
            if use_pools:
                with tab_objs[3]: ui_tournament_pools_view(t["id"])
                with tab_objs[4]: ui_tournament_results_view(t["id"])
                with tab_objs[5]: ui_tournament_standings(t["id"])
            else:
                with tab_objs[3]: ui_tournament_results_view(t["id"])
                with tab_objs[4]: ui_tournament_standings(t["id"])
        st.write("")

def ui_profile_page():
    require_login(); user = st.session_state["user"]
    st.subheader(f"👤 Trang cá nhân: {user['full_name']}")
    tab_info, tab_rank = st.tabs(["Thông tin cá nhân", "Bảng xếp hạng cá nhân"])
    with tab_rank:
        owner_id = user["id"]; existing = get_personal_ranking(owner_id)
        players = [p for p in get_all_players(only_approved=True) if p["id"] != owner_id]
        if not players: st.info("Chưa có đủ thành viên."); return
        if not existing:
            st.info("Chưa có BXH cá nhân.")
            if st.button("Tạo BXH tự động", type="primary"):
                order_ids = get_hnpr_order_or_alpha(); order_ids = [uid for uid in order_ids if uid != owner_id]
                save_personal_ranking(owner_id, order_ids); st.success("Đã tạo."); st.rerun()
            return
        if "personal_order" not in st.session_state: st.session_state["personal_order"] = [r["ranked_user_id"] for r in existing]
        order = st.session_state["personal_order"]
        for i, uid in enumerate(order):
            player = next((p for p in players if p["id"] == uid), None)
            if not player: continue
            cols = st.columns([0.1, 0.6, 0.1, 0.1])
            cols[0].write(f"#{i + 1}"); cols[1].write(player["full_name"])
            if cols[2].button("⬆", key=f"up_{uid}_{i}") and i > 0: order[i-1], order[i] = order[i], order[i-1]; st.session_state["personal_order"] = order; st.rerun()
            if cols[3].button("⬇", key=f"down_{uid}_{i}") and i < len(order)-1: order[i+1], order[i] = order[i], order[i+1]; st.session_state["personal_order"] = order; st.rerun()
        st.markdown("---")
        c1, c2 = st.columns(2)
        if c1.button("💾 Lưu BXH", type="primary", use_container_width=True): save_personal_ranking(owner_id, order); st.success("Đã lưu.")
        if c2.button("🗑️ Xoá BXH", use_container_width=True): delete_personal_ranking(owner_id); st.session_state.pop("personal_order", None); st.rerun()
    with tab_info:
        col_form, _ = st.columns([1, 1])
        with col_form:
            full_name = st.text_input("Họ tên", value=user["full_name"])
            age = st.number_input("Tuổi", min_value=5, max_value=100, value=user.get("age") or 30, step=1)
            new_password = st.text_input("Đổi mật khẩu", type="password")
            if st.button("💾 Lưu thông tin", type="primary"):
                conn = get_conn(); cur = conn.cursor()
                if new_password: cur.execute("UPDATE users SET full_name = ?, age = ?, password_hash = ? WHERE id = ?", (full_name, age, hash_password(new_password), user["id"]))
                else: cur.execute("UPDATE users SET full_name = ?, age = ? WHERE id = ?", (full_name, age, user["id"]))
                conn.commit(); conn.close(); st.session_state["user"] = dict(get_user_by_id(user["id"])); st.success("Đã cập nhật.")
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            delete_session_token(st.session_state.get("login_token"))
            st.session_state["user"] = None; st.session_state["login_token"] = None; st.query_params = {}; st.rerun()

def ui_tournament_page():
    require_role(["admin", "btc"])
    if "tournament_view_mode" not in st.session_state: st.session_state["tournament_view_mode"] = "list"
    if st.session_state["tournament_view_mode"] == "detail" and st.session_state["selected_tournament_id"]:
        ui_tournament_detail_page(st.session_state["selected_tournament_id"])
    else: ui_tournament_list_page()

def ui_tournament_list_page():
    st.subheader("🛠️ Quản lý giải đấu")
    if "show_create_t" not in st.session_state: st.session_state["show_create_t"] = False
    tournaments = get_tournaments()
    if tournaments and not st.session_state["show_create_t"]:
        st.markdown(f"**Danh sách giải ({len(tournaments)})**")
        cols = st.columns([0.05, 0.25, 0.15, 0.2, 0.1, 0.15, 0.1])
        cols[0].markdown("**ID**"); cols[1].markdown("**Tên giải**"); cols[2].markdown("**Thể loại**"); cols[3].markdown("**Thời gian**"); cols[4].markdown("**Active**"); cols[5].markdown("**Thao tác**")
        st.markdown("---")
        for t in tournaments:
            tid = t["id"]; ctype = t["competition_type"] if t["competition_type"] in ("pair", "team") else "pair"
            c = st.columns([0.05, 0.25, 0.15, 0.2, 0.1, 0.15, 0.1])
            c[0].write(tid); c[1].write(t["name"]); c[2].write("Cặp" if ctype == "pair" else "Đội"); c[3].write(f"{t['start_date'] or ''}"); c[4].markdown("✅" if t["is_active"] else "")
            with c[5]:
                b1, b2, b3 = st.columns(3)
                if b1.button("👁", key=f"v_{tid}"): st.session_state["tournament_view_mode"] = "detail"; st.session_state["selected_tournament_id"] = tid; st.rerun()
                if b2.button("✏", key=f"e_{tid}"): st.session_state["editing_tournament_id"] = tid; st.session_state["show_create_t"] = True; st.rerun()
                if b3.button("🗑", key=f"d_{tid}"): delete_tournament(tid); st.rerun()
        st.markdown("---")

    if not st.session_state["show_create_t"]:
        if st.button("➕ Thêm giải mới", type="primary"): st.session_state["show_create_t"] = True; st.rerun()
        return

    with st.container():
        st.markdown("### 📝 Thông tin giải đấu")
        editing_id = st.session_state.get("editing_tournament_id")
        if editing_id:
            t = get_tournament_by_id(editing_id)
            d_name = t["name"]; d_start = t["start_date"]; d_end = t["end_date"]; d_loc = t["location"]; d_nc = t["num_courts"] or 4; d_act = bool(t["is_active"]); d_ctype = t.get("competition_type", "pair"); d_pool = bool(t.get("use_pools", 1)); d_adv = t.get("adv_per_pool")
        else: d_name = ""; d_start = ""; d_end = ""; d_loc = ""; d_nc = 4; d_act = False; d_ctype = "pair"; d_pool = True; d_adv = None

        with st.form("tournament_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Tên giải", value=d_name)
                location = st.text_input("Địa điểm", value=d_loc)
                num_courts = st.number_input("Số sân", 1, 20, d_nc)
            with col2:
                c_d1, c_d2 = st.columns(2)
                start_date = c_d1.text_input("Ngày bắt đầu", value=d_start or "")
                end_date = c_d2.text_input("Ngày kết thúc", value=d_end or "")
                ctype = st.radio("Thể loại", ["Theo cặp", "Theo đội"], index=0 if d_ctype == "pair" else 1, horizontal=True)
                use_pools = st.checkbox("Có phân bảng", value=d_pool); is_active = st.checkbox("Đang diễn ra", value=d_act)
            st.markdown("---")
            c_s, c_c = st.columns([1, 1])
            if c_s.form_submit_button("💾 Lưu", type="primary", use_container_width=True):
                if not name: st.warning("Nhập tên giải")
                else:
                    upsert_tournament(editing_id, name, start_date, end_date, location, num_courts, is_active, "pair" if ctype=="Theo cặp" else "team", use_pools, d_adv)
                    st.success("Đã lưu."); st.session_state["editing_tournament_id"] = None; st.session_state["show_create_t"] = False; st.rerun()
            if c_c.form_submit_button("Huỷ", use_container_width=True):
                st.session_state["editing_tournament_id"] = None; st.session_state["show_create_t"] = False; st.rerun()

def ui_tournament_detail_page(t_id: int):
    t = get_tournament_by_id(t_id)
    if not t: st.session_state["tournament_view_mode"] = "list"; st.rerun()
    if st.button("⬅ Quay lại", use_container_width=False): st.session_state["tournament_view_mode"] = "list"; st.rerun()
    ctype = t["competition_type"] if "competition_type" in t.keys() else "pair"
    use_pools = bool(t["use_pools"])
    st.markdown(f"## ⚙️ Quản lý: {t['name']}")
    st.markdown(f"""
    <div class="info-grid" style="margin-bottom: 20px;">
        <div class="info-item"><span class="info-label">📍 Địa điểm</span><span class="info-value">{t['location'] or 'N/A'}</span></div>
        <div class="info-item"><span class="info-label">📅 Thời gian</span><span class="info-value">{t['start_date']}</span></div>
        <div class="info-item"><span class="info-label">🎾 Thể thức</span><span class="info-value">{'Theo Cặp' if ctype == 'pair' else 'Theo Đội'}</span></div>
        <div class="info-item"><span class="info-label">🔥 Trạng thái</span><span class="info-value">{'Đang chạy' if t['is_active'] else 'Inactive'}</span></div>
    </div>
    """, unsafe_allow_html=True)
    pair_team_label = "Chia cặp" if ctype == "pair" else "Chia đội"
    tabs_list = ["Thành viên", "Phân nhóm", pair_team_label, "Phân bảng", "Lịch & KQ", "Xếp hạng"] if use_pools else ["Thành viên", "Phân nhóm", pair_team_label, "Lịch & KQ", "Xếp hạng"]
    tabs = st.tabs(tabs_list)
    with tabs[0]: ui_tournament_players(t_id)
    with tabs[1]: ui_tournament_groups(t_id)
    with tabs[2]: ui_tournament_pairs_teams(t_id)
    if use_pools:
        with tabs[3]: ui_tournament_pools(t_id)
        with tabs[4]: ui_tournament_results(t_id)
        with tabs[5]: ui_tournament_standings(t_id)
    else:
        with tabs[3]: ui_tournament_results(t_id)
        with tabs[4]: ui_tournament_standings(t_id)

def ui_tournament_players_view(t_id):
    current = get_tournament_players(t_id)
    if current:
        st.write(f"**Tham gia ({len(current)})**")
        cols = st.columns(4)
        for i, p in enumerate(current): cols[i % 4].markdown(f"👤 {p['full_name']}")
    else: st.info("Chưa có VĐV.")

def ui_tournament_players(t_id):
    current = get_tournament_players(t_id)
    st.markdown("#### 1. Thành viên tham gia")
    if current:
        st.success(f"Hiện có **{len(current)}** VĐV.")
        with st.expander("Chi tiết"):
            cols = st.columns(4)
            for i, p in enumerate(current): cols[i % 4].write(f"- {p['full_name']}")
    else: st.info("Chưa có thành viên.")
    flag_key = f"show_add_players_{t_id}"
    if flag_key not in st.session_state: st.session_state[flag_key] = False
    if not st.session_state[flag_key]:
        if st.button("➕ Thêm / Sửa", key=f"btn_add_{t_id}"): st.session_state[flag_key] = True; st.rerun()
    else:
        if st.button("Huỷ", key=f"btn_hide_{t_id}"): st.session_state[flag_key] = False; st.rerun()
        st.write("Chọn thành viên:")
        all_p = get_all_players(only_approved=True)
        cur_ids = {p["user_id"] for p in current}; sel_ids = set(cur_ids)
        with st.form(f"p_form_{t_id}"):
            cols = st.columns(4)
            for i, p in enumerate(all_p):
                if cols[i%4].checkbox(f"{p['full_name']}", value=p["id"] in cur_ids, key=f"chk_{t_id}_{p['id']}"): sel_ids.add(p["id"])
                else: sel_ids.discard(p["id"])
            if st.form_submit_button("💾 Lưu", type="primary"): set_tournament_players(t_id, list(sel_ids)); st.session_state[flag_key] = False; st.rerun()

def ui_tournament_groups_view(t_id):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT tp.user_id, tp.group_name, u.full_name FROM tournament_players tp JOIN users u ON u.id = tp.user_id WHERE tp.tournament_id = ? ORDER BY tp.group_name, u.full_name", (t_id,))
    rows = cur.fetchall(); conn.close()
    if not rows: st.info("Chưa phân nhóm."); return
    g_map = {}
    for r in rows: g_map.setdefault(r["group_name"] or "N/A", []).append(r["full_name"])
    cols = st.columns(len(g_map) if g_map else 1)
    for i, (g, names) in enumerate(sorted(g_map.items())):
        with cols[i%4]:
            st.info(f"**Nhóm {g}** ({len(names)})")
            for n in names: st.markdown(f"• {n}")

def ui_tournament_groups(t_id):
    players = get_tournament_players(t_id)
    if not players:
        st.warning("Thêm thành viên trước.")
        return

    st.markdown("#### 2. Cấu hình phân nhóm")

    # --- Cấu hình số nhóm, tên nhóm, số VĐV mỗi nhóm ---
    c1, c2 = st.columns([1, 2])
    num = c1.number_input("Số nhóm", 1, 8, 4, key=f"ng_{t_id}")
    g_defs = []
    for i in range(int(num)):
        c_a, c_b = st.columns([1, 1])
        gn = c_a.text_input(f"Tên {i+1}", chr(ord('A') + i), key=f"gn_{t_id}_{i}")
        gs = c_b.number_input(
            f"Số lượng thành viên nhóm {gn}",
            1,
            len(players),
            max(1, len(players) // int(num)),
            key=f"gs_{t_id}_{i}",
        )
        g_defs.append((gn, int(gs)))

    # --- Chọn nguồn xếp hạng để phân nhóm ---
    st.markdown("##### Nguồn xếp hạng dùng để phân nhóm tự động")
    ranking_source = st.radio(
        "",
        ["HNPR (BXH cá nhân)", "BXH BTC (Ban tổ chức)"],
        index=0,
        horizontal=True,
        key=f"rank_source_{t_id}",
    )

    c_x, c_y = st.columns(2)

    # Nút phân nhóm tự động
    if c_x.button("⚡ Phân nhóm tự động"):
        player_ids = [p["user_id"] for p in players]
        order_ids = []

        # Ưu tiên dùng BXH BTC nếu được chọn
        if ranking_source.startswith("BXH BTC"):
            btc_rank = get_btc_ranking()
            if btc_rank:
                order_ids = [
                    r["ranked_user_id"]
                    for r in btc_rank
                    if r["ranked_user_id"] in player_ids
                ]

        # Nếu không có BTC hoặc không phù hợp -> fallback sang HNPR
        if not order_ids:
            hnpr = compute_hnpr()
            if hnpr:
                order_ids = [
                    r["user_id"]
                    for r in hnpr
                    if r["user_id"] in player_ids
                ]

        # Nếu vẫn không có -> fallback ABC
        if not order_ids:
            players_sorted_alpha = sorted(players, key=lambda p: p["full_name"])
            order_ids = [p["user_id"] for p in players_sorted_alpha]

        # rank_map: user_id -> thứ tự (càng nhỏ càng mạnh)
        rank_map = {uid: idx for idx, uid in enumerate(order_ids)}

        # Sắp xếp danh sách VĐV theo thứ tự rank_map
        players_sorted = sorted(
            players,
            key=lambda p: rank_map.get(p["user_id"], 9999),
        )

        # Gán vào các nhóm theo cấu hình g_defs
        assigned = {}
        idx = 0
        for name, size in g_defs:
            for _ in range(size):
                if idx >= len(players_sorted):
                    break
                assigned[players_sorted[idx]["user_id"]] = name
                idx += 1

        conn = get_conn()
        cur = conn.cursor()
        for uid, gn in assigned.items():
            cur.execute(
                "UPDATE tournament_players SET group_name = ? WHERE tournament_id = ? AND user_id = ?",
                (gn, t_id, uid),
            )
        conn.commit()
        conn.close()
        st.success("Đã phân nhóm.")
        st.rerun()

    # Nút xoá phân nhóm
    if c_y.button("🗑 Xóa phân nhóm"):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE tournament_players SET group_name = NULL WHERE tournament_id = ?",
            (t_id,),
        )
        conn.commit()
        conn.close()
        st.rerun()

    ui_tournament_groups_view(t_id)

def make_pairs_for_tournament(t_id):
    players = get_tournament_players(t_id)
    if len(players) < 2: st.warning("Cần >= 2 VĐV."); return
    g_map = {}
    for p in players: g_map.setdefault(p["group_name"] or "", []).append(p)
    groups = sorted(g_map.keys(), key=lambda x: (x == "", x))
    clear_competitors_and_matches(t_id)
    conn = get_conn()
    if len([g for g in groups if g]) >= 2:
        g_list = sorted([g for g in groups if g])
        random.seed()
        for i in range(len(g_list)//2):
            hi = g_map[g_list[i]][:]; lo = g_map[g_list[-i-1]][:]
            random.shuffle(hi); random.shuffle(lo)
            for k in range(min(len(hi), len(lo))): create_competitor(conn, t_id, [hi[k]["user_id"], lo[k]["user_id"]])
    else:
        hnpr = compute_hnpr(); s_map = {r["user_id"]: r["avg_pos"] for r in hnpr}
        p_sorted = sorted(players, key=lambda p: s_map.get(p["user_id"], 9999))
        n = len(p_sorted); half = n//2; top = p_sorted[:half]; bot = p_sorted[half:]; random.shuffle(top); random.shuffle(bot)
        for i in range(min(len(top), len(bot))): create_competitor(conn, t_id, [top[i]["user_id"], bot[i]["user_id"]])
    conn.commit(); conn.close()

def make_teams_for_tournament(t_id, num_teams):
    players = get_tournament_players(t_id)
    if len(players) < num_teams: st.warning("Số đội > VĐV."); return
    hnpr = compute_hnpr(); s_map = {r["user_id"]: r["avg_pos"] for r in hnpr}
    def g_idx(g): return ord(g[0].upper()) - ord('A') if g else 99
    p_sorted = sorted(players, key=lambda p: (g_idx(p["group_name"]), s_map.get(p["user_id"], 9999)))
    random.shuffle(p_sorted)
    t_mems = {i: [] for i in range(num_teams)}; idx = 0
    for p in p_sorted: t_mems[idx].append(p["user_id"]); idx = (idx+1)%num_teams
    clear_competitors_and_matches(t_id)
    conn = get_conn(); cur = conn.cursor()
    for i in range(num_teams):
        cur.execute("INSERT INTO competitors (tournament_id, name, kind) VALUES (?, ?, 'team')", (t_id, f"Đội {i+1}"))
        cid = cur.lastrowid
        for uid in t_mems[i]: cur.execute("INSERT INTO competitor_members (competitor_id, user_id) VALUES (?, ?)", (cid, uid))
    conn.commit(); conn.close()

def ui_tournament_pairs_teams_view(t_id):
    t = get_tournament_by_id(t_id); ctype = t["competition_type"] if "competition_type" in t.keys() else "pair"
    comps = get_competitors(t_id); m_map = get_competitor_members_map(t_id)
    if not comps: st.info("Chưa có danh sách thi đấu."); return
    if ctype == "team":
        for c in comps:
            mn = [m[1] for m in m_map.get(c["id"], [])]
            with st.expander(f"🏅 {c['name']}"): st.write(", ".join(mn))
    else:
        st.write("**Cặp đấu:**")
        cols = st.columns(3)
        for i, c in enumerate(comps): cols[i%3].success(f"🎾 {build_competitor_display_name(c['id'], m_map)}")

def ui_tournament_pairs_teams(t_id):
    t = get_tournament_by_id(t_id); ctype = t["competition_type"] if "competition_type" in t.keys() else "pair"
    st.markdown(f"#### 3. Tạo {'Cặp' if ctype == 'pair' else 'Đội'} thi đấu")
    if ctype == "pair":
        if st.button("⚡ Ghép cặp tự động", type="primary"): make_pairs_for_tournament(t_id); st.success("Xong."); st.rerun()
    else:
        c1, c2 = st.columns([1, 2])
        nt = c1.number_input("Số đội", 2, 16, 4)
        if c2.button("⚡ Chia đội tự động", type="primary"): make_teams_for_tournament(t_id, int(nt)); st.success("Xong."); st.rerun()
    ui_tournament_pairs_teams_view(t_id)

def ui_tournament_pools_view(t_id):
    comps = get_competitors(t_id); m_map = get_competitor_members_map(t_id)
    p_map = {}
    for c in comps: p_map.setdefault(c["pool_name"] or "N/A", []).append(build_competitor_display_name(c["id"], m_map))
    if not p_map: return
    st.write("### 🎱 Danh sách Bảng")
    cols = st.columns(len(p_map) if len(p_map) <= 4 else 4)
    for i, (pn, ns) in enumerate(sorted(p_map.items())):
        with cols[i%4]:
            st.markdown(f"**Bảng {pn}**")
            for n in ns: st.markdown(f"- {n}")

def ui_tournament_pools(t_id):
    t = get_tournament_by_id(t_id); comps = get_competitors(t_id)
    if not comps: st.warning("Tạo cặp/đội trước."); return
    adv = t["adv_per_pool"] or 1
    st.markdown("#### 4. Phân bảng")
    c1, c2, c3 = st.columns([1, 1, 1])
    np = c1.number_input("Số bảng", 1, 16, 4)
    ap = c2.number_input("Đi tiếp/bảng", 1, 8, int(adv))
    if c3.button("⚡ Phân bảng tự động"):
        pns = [chr(ord('A')+i) for i in range(int(np))]
        conn = get_conn(); cur = conn.cursor()
        for i, c in enumerate(comps): cur.execute("UPDATE competitors SET pool_name = ? WHERE id = ?", (pns[i%len(pns)], c["id"]))
        cur.execute("UPDATE tournaments SET adv_per_pool = ? WHERE id = ?", (int(ap), t_id))
        conn.commit(); conn.close(); st.success("Xong."); st.rerun()
    ui_tournament_pools_view(t_id)

def ui_tournament_results_view(t_id):
    st.markdown("### 📅 Lịch & Kết quả")
    t = get_tournament_by_id(t_id); ctype = t["competition_type"] if "competition_type" in t.keys() else "pair"
    matches = get_matches(t_id); m_map = get_competitor_members_map(t_id)
    if not matches: st.info("Chưa có trận đấu."); return
    for m in matches:
        if ctype == "team":
            def gn(p1, p2): return ", ".join([get_user_by_id(uid)["full_name"] for uid in [p1, p2] if uid])
            n1 = f"{m['name1']} <br><small>({gn(m['team1_p1_id'], m['team1_p2_id'])})</small>"
            n2 = f"{m['name2']} <br><small>({gn(m['team2_p1_id'], m['team2_p2_id'])})</small>"
        else:
            n1 = build_competitor_display_name(m["competitor1_id"], m_map)
            n2 = build_competitor_display_name(m["competitor2_id"], m_map)
        st.markdown(f"""
        <div style="background:white; padding:15px; border-radius:8px; border:1px solid #eee; margin-bottom:10px; box-shadow:0 1px 2px rgba(0,0,0,0.03);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="text-align:right; width:40%; font-weight:600; color:#333;">{n1}</div>
                <div style="background:#F3F4F6; color:#333; padding:5px 15px; border-radius:20px; font-weight:bold; border:1px solid #e5e7eb;">{m['score1']} - {m['score2']}</div>
                <div style="text-align:left; width:40%; font-weight:600; color:#333;">{n2}</div>
            </div>
        </div>""", unsafe_allow_html=True)

def ui_tournament_results(t_id):
    t = get_tournament_by_id(t_id); ctype = t["competition_type"] if "competition_type" in t.keys() else "pair"
    comps = get_competitors(t_id); m_map = get_competitor_members_map(t_id)
    if not comps: return
    with st.expander("📝 Nhập kết quả", expanded=True):
        labels = []; c_map = {}
        for c in comps:
            lbl = c["name"] if c["kind"]=="team" else build_competitor_display_name(c["id"], m_map)
            labels.append(lbl); c_map[lbl] = c["id"]
        c1, c2 = st.columns(2); s1 = c1.selectbox("Đội 1", labels, key=f"s1_{t_id}"); s2 = c2.selectbox("Đội 2", labels, key=f"s2_{t_id}")
        tp = None; t1i = []; t2i = []
        if ctype == "team":
            cc1, cc2 = st.columns(2)
            with cc1:
                st.write(f"**{s1}**")
                for uid, n in m_map.get(c_map[s1], []):
                    if st.checkbox(n, key=f"t1_{uid}"): t1i.append(uid)
            with cc2:
                st.write(f"**{s2}**")
                for uid, n in m_map.get(c_map[s2], []):
                    if st.checkbox(n, key=f"t2_{uid}"): t2i.append(uid)
        sc1, sc2 = st.columns(2); scr1 = sc1.number_input("Điểm 1", 0, 100, 11); scr2 = sc2.number_input("Điểm 2", 0, 100, 9)
        if st.button("Lưu KQ", type="primary"):
            cid1 = c_map[s1]; cid2 = c_map[s2]
            if cid1 == cid2: st.error("Trùng đội."); return
            if ctype == "team" and (len(t1i)!=2 or len(t2i)!=2): st.error("Chọn đúng 2 VĐV/đội."); return
            if ctype == "team": tp = (t1i[0], t1i[1], t2i[0], t2i[1])
            add_match(t_id, cid1, cid2, int(scr1), int(scr2), st.session_state["user"]["id"], True, tp)
            st.success("Lưu thành công."); st.rerun()
    ui_tournament_results_view(t_id)

def ui_tournament_standings(t_id):
    t = get_tournament_by_id(t_id); use_pools = bool(t["use_pools"]); adv = t["adv_per_pool"]; m_map = get_competitor_members_map(t_id)
    st.markdown("### 🏆 Bảng xếp hạng")
    if use_pools:
        ps = compute_pool_standings(t_id)
        if not ps: st.info("Chưa có dữ liệu."); return
        for pn, lst in sorted(ps.items()):
            st.markdown(f"**Bảng {pn}**")
            q_ids = {item["id"] for item in lst[:int(adv)]} if adv else set()
            rows = []
            for i, s in enumerate(lst):
                rows.append({"Hạng": i+1, "Tên": build_competitor_display_name(s["id"], m_map), "Thắng": s["wins"], "Hiệu số": s["diff"], "Ghi/Thủng": f"{s['pts_for']}/{s['pts_against']}", "Note": "✅ Đi tiếp" if s["id"] in q_ids else ""})
            st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        std = compute_standings(t_id)
        if std:
            rows = [{"Hạng": i+1, "Tên": build_competitor_display_name(s["id"], m_map), "Thắng": s["wins"], "Hiệu số": s["diff"], "Ghi/Thủng": f"{s['pts_for']}/{s['pts_against']}"} for i, s in enumerate(std)]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else: st.info("Chưa có dữ liệu.")

# ------------------ Main app ------------------ #

def main():
    init_db()
    params = st.query_params; token = params.get("t"); token = token[0] if isinstance(token, list) else token
    if st.session_state["user"] is None and token:
        u = get_user_by_session_token(token)
        if u: st.session_state["user"] = dict(u); st.session_state["login_token"] = token

    user = st.session_state["user"]
    
    # --- HEADER ---
    c_logo, c_title, c_user = st.columns([0.8, 7, 2])
    c_logo.markdown("<div style='font-size:2.5rem; text-align:center;'>🏓</div>", unsafe_allow_html=True)
    c_title.markdown("<h1 style='margin:0; font-size: 1.8rem; padding-top:5px; color:#111827;'>HNX Pickleball Allstars</h1>", unsafe_allow_html=True)
    if user: c_user.markdown(f"<div style='text-align:right; padding-top:15px; font-size:0.9rem;'>Hi, <b>{user['full_name']}</b></div>", unsafe_allow_html=True)
    #st.markdown("---")

    # --- MENU CHÍNH ---
    tabs_list = ["Trang chủ", "Bảng xếp hạng"]
    if not user: tabs_list.append("Đăng nhập")
    else:
        if user.get("is_admin") or user.get("is_btc"): tabs_list.extend(["Thành viên", "Giải đấu"])
        tabs_list.append("Cá nhân")

    # Bọc tabs trong class đặc biệt để CSS style "Pills"
    st.markdown('<div class="main-menu-tabs">', unsafe_allow_html=True)
    selected_tabs = st.tabs(tabs_list)
    st.markdown('</div>', unsafe_allow_html=True)

    with selected_tabs[0]: ui_home()
    with selected_tabs[1]: ui_hnpr_page()
    
    if not user:
        with selected_tabs[2]: ui_login_register()
    else:
        idx = 2
        if user.get("is_admin") or user.get("is_btc"):
            with selected_tabs[idx]: ui_member_management()
            with selected_tabs[idx+1]: ui_tournament_page()
            idx += 2
        with selected_tabs[idx]: ui_profile_page()

if __name__ == "__main__":
    main()