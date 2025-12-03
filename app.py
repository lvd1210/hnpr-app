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
        margin-bottom: 0px;
    }

    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
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
            
    @media (max-width: 768px) {
        /* Thu nhỏ padding, cho đỡ tốn chỗ */
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }

        /* Card giải đấu gọn hơn */
        .tournament-card {
            padding: 12px;
            margin-bottom: 12px;
        }

        /* Tabs chính: cho tràn ngang + chữ nhỏ đi */
        .main-menu-tabs div[data-baseweb="tab-list"] {
            overflow-x: auto;
            white-space: nowrap;
            padding: 4px 0 0 0 !important;
            gap: 4px;
        }

        .main-menu-tabs div[data-baseweb="tab"] {
            padding: 6px 10px !important;
            font-size: 0.85rem !important;
        }

        /* Tabs con cũng nhỏ lại xíu */
        div[data-baseweb="tab-list"] {
            gap: 12px;
        }
        div[data-baseweb="tab"] {
            font-size: 0.85rem;
            padding-bottom: 6px;
        }

        /* Các list dùng st.columns(...) -> cho xếp dọc 100% width */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }
        [data-testid="column"] {
            width: 100% !important;
            padding-right: 0 !important;
        }

        /* Dataframe bớt cao */
        .css-1n76uvr, .css-1dp5vir {
            max-height: 360px;
        }
    }
            
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Ép tất cả hàng dạng columns không bị xuống dòng */
.no-wrap-row {
    display: flex !important;
    flex-direction: row !important;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    white-space: nowrap;             /* Không cho xuống dòng trong text */
}
.no-wrap-row > div {
    flex: 1 1 auto !important;       /* Các cột vẫn co giãn nhưng không wrap */
    min-width: 0 !important;         /* Giúp co lại thay vì đẩy xuống hàng */
}

/* Nếu dùng trong danh sách thẻ (list item) thì thêm: */
.list-item {
    padding: 6px 10px;
    border-bottom: 1px solid #eee;
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER,
            role TEXT NOT NULL DEFAULT 'player',
            is_approved INTEGER NOT NULL DEFAULT 0,
            is_btc INTEGER NOT NULL DEFAULT 0,
            is_admin INTEGER NOT NULL DEFAULT 0,
            gender TEXT,
            unit TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            location TEXT,
            num_courts INTEGER,
            is_active INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Bổ sung cột mới cho bảng tournaments nếu thiếu
    cur.execute("PRAGMA table_info(tournaments)")
    cols = [r[1] for r in cur.fetchall()]
    if "competition_type" not in cols:
        cur.execute("ALTER TABLE tournaments ADD COLUMN competition_type TEXT")
    if "use_pools" not in cols:
        cur.execute("ALTER TABLE tournaments ADD COLUMN use_pools INTEGER NOT NULL DEFAULT 1")
    if "adv_per_pool" not in cols:
        cur.execute("ALTER TABLE tournaments ADD COLUMN adv_per_pool INTEGER")

    # BỔ SUNG CỘT gender, unit CHO BẢNG users NẾU DB CŨ CHƯA CÓ
    cur.execute("PRAGMA table_info(users)")
    ucols = [r[1] for r in cur.fetchall()]
    if "gender" not in ucols:
        cur.execute("ALTER TABLE users ADD COLUMN gender TEXT")
    if "unit" not in ucols:
        cur.execute("ALTER TABLE users ADD COLUMN unit TEXT")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tournament_players (
            tournament_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'approved',
            group_name TEXT,
            PRIMARY KEY (tournament_id, user_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS personal_ranking_items (
            owner_id INTEGER NOT NULL,
            ranked_user_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            PRIMARY KEY (owner_id, ranked_user_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS btc_ranking_items (
            ranked_user_id INTEGER PRIMARY KEY,
            position      INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            pool_name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS competitor_members (
            competitor_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (competitor_id, user_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            competitor1_id INTEGER NOT NULL,
            competitor2_id INTEGER NOT NULL,
            score1 INTEGER NOT NULL,
            score2 INTEGER NOT NULL,
            winner_id INTEGER NOT NULL,
            reported_by INTEGER,
            confirmed_by INTEGER
        )
    """)

    cur.execute("PRAGMA table_info(matches)")
    mcols = [r[1] for r in cur.fetchall()]
    if "team1_p1_id" not in mcols:
        cur.execute("ALTER TABLE matches ADD COLUMN team1_p1_id INTEGER")
    if "team1_p2_id" not in mcols:
        cur.execute("ALTER TABLE matches ADD COLUMN team1_p2_id INTEGER")
    if "team2_p1_id" not in mcols:
        cur.execute("ALTER TABLE matches ADD COLUMN team2_p1_id INTEGER")
    if "team2_p2_id" not in mcols:
        cur.execute("ALTER TABLE matches ADD COLUMN team2_p2_id INTEGER")

    conn.commit()

    # Kiểm tra xem user 'admin' đã tồn tại chưa
    cur.execute("SELECT * FROM users WHERE username = 'admin'")
    admin_user = cur.fetchone()

    if admin_user is None:
        # Chưa có admin -> tạo mới
        password_hash = hash_password("admin")
        cur.execute("""
            INSERT INTO users (
                username, password_hash, full_name, age,
                role, is_approved, is_btc, is_admin,
                gender, unit, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "admin",
            password_hash,
            "Administrator",
            0,
            "admin",
            1,   # is_approved
            1,   # is_btc
            1,   # is_admin
            "Nam",    # gender mặc định
            "Ban tổ chức",  # unit mặc định
            datetime.utcnow().isoformat()
        ))
        conn.commit()
    else:
        # ĐÃ tồn tại user admin -> cập nhật quyền lại cho chắc
        cur.execute("""
            UPDATE users
            SET role = 'admin',
                is_admin = 1,
                is_btc = 1,
                is_approved = 1
            WHERE username = 'admin'
        """)
        conn.commit()

    conn.close()


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

def ranking_sortable_combined(order_ids, id_to_player, key_prefix: str):
    """
    Danh sách duy nhất, có:
    - Drag & drop
    - Nút ⬆ ⬇ ngay trên chính danh sách đó
    """

    # SESSION STATE -------------------------
    skey = f"{key_prefix}_order"
    if skey not in st.session_state:
        st.session_state[skey] = list(order_ids)
    else:
        # Đồng bộ nếu có người mới
        cur = st.session_state[skey]
        for uid in order_ids:
            if uid not in cur:
                cur.append(uid)
        valid = set(order_ids)
        cur = [uid for uid in cur if uid in valid]
        st.session_state[skey] = cur

    working = st.session_state[skey]

    # TẠO LABEL KÉO THẢ ---------------------
    labels = []
    uid_map = {}   # label -> uid

    for idx, uid in enumerate(working, start=1):
        p = id_to_player[uid]
        label = f"{idx}. {p['full_name']}"
        labels.append(label)
        uid_map[label] = uid

    st.caption("Kéo–thả để sắp xếp. Hoặc dùng nút ⬆ ⬇ để đổi nhanh.")

    # KÉO THẢ -------------------------------
    new_labels = sort_items(
        labels,
        direction="vertical",
        key=f"{key_prefix}_sort"
    )

    # MAP NGƯỢC LẠI --------------------------------
    new_order = [uid_map[lbl] for lbl in new_labels]

    # CẬP NHẬT SESSION
    st.session_state[skey] = new_order

    # HIỂN THỊ DANH SÁCH + NÚT UP/DOWN ----------------
    for i, uid in enumerate(new_order):
        p = id_to_player[uid]
        col1, col2, col3, col4 = st.columns([0.1, 0.7, 0.1, 0.1])
        with col1:
            st.write(f"{i+1}.")
        with col2:
            st.write(p["full_name"])

        # NÚT UP
        with col3:
            if st.button("⬆", key=f"{key_prefix}_up_{uid}", help="Đẩy lên") and i > 0:
                new_order[i-1], new_order[i] = new_order[i], new_order[i-1]
                st.session_state[skey] = new_order
                st.rerun()

        # NÚT DOWN
        with col4:
            if st.button("⬇", key=f"{key_prefix}_down_{uid}", help="Đẩy xuống") and i < len(new_order)-1:
                new_order[i+1], new_order[i] = new_order[i], new_order[i+1]
                st.session_state[skey] = new_order
                st.rerun()

    return new_order

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
    if "is_admin" in roles and is_admin: ok = True
    if "is_btc" in roles and (is_btc or is_admin): ok = True
    if "player" in roles: ok = True
    if not ok:
        st.error("⛔ Bạn không có quyền truy cập.")
        st.stop()

# ------------------ Logic & Data Access ------------------ #

def get_all_players(only_approved=True, include_admin=False):
    """
    Lấy danh sách người chơi:
    - only_approved = True  => chỉ lấy user đã được duyệt
    - include_admin = False => loại admin ra (is_admin = 0)
    """
    conn = get_conn()
    cur = conn.cursor()

    if only_approved:
        if include_admin:
            # Tất cả user đã duyệt, kể cả admin
            cur.execute(
                "SELECT * FROM users WHERE is_approved = 1 ORDER BY full_name"
            )
        else:
            # Thành viên đã duyệt, TRỪ admin
            cur.execute(
                """
                SELECT * FROM users
                WHERE is_approved = 1
                  AND (is_admin IS NULL OR is_admin = 0)
                ORDER BY full_name
                """
            )
    else:
        if include_admin:
            cur.execute("SELECT * FROM users ORDER BY full_name")
        else:
            cur.execute(
                """
                SELECT * FROM users
                WHERE (is_admin IS NULL OR is_admin = 0)
                ORDER BY full_name
                """
            )

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

def get_tournament_players(tournament_id, approved_only: bool = True):
    """
    Lấy danh sách VĐV của giải.
    Mặc định chỉ lấy VĐV đã được duyệt (status = 'approved').
    """
    conn = get_conn()
    cur = conn.cursor()
    if approved_only:
        cur.execute(
            """
            SELECT
                tp.tournament_id,
                tp.user_id,
                tp.status,
                tp.group_name,
                u.full_name,
                u.gender
            FROM tournament_players tp
            JOIN users u ON u.id = tp.user_id
            WHERE tp.tournament_id = ? AND tp.status = 'approved'
            ORDER BY u.full_name
            """,
            (tournament_id,),
        )
    else:
        cur.execute(
            """
            SELECT
                tp.tournament_id,
                tp.user_id,
                tp.status,
                tp.group_name,
                u.full_name,
                u.gender
            FROM tournament_players tp
            JOIN users u ON u.id = tp.user_id
            WHERE tp.tournament_id = ?
            ORDER BY u.full_name
            """,
            (tournament_id,),
        )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_tournament_pending_players(tournament_id):
    """
    Lấy danh sách VĐV đang chờ duyệt (status = 'pending').
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            tp.tournament_id,
            tp.user_id,
            tp.status,
            tp.group_name,
            u.full_name
        FROM tournament_players tp
        JOIN users u ON u.id = tp.user_id
        WHERE tp.tournament_id = ? AND tp.status = 'pending'
        ORDER BY u.full_name
        """,
        (tournament_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def set_tournament_players(tournament_id, user_ids):
    """
    Cập nhật danh sách VĐV đã được duyệt (approved) cho giải.
    - Xoá toàn bộ bản ghi status='approved' của giải
    - Thêm (hoặc thay thế) bản ghi mới cho các user_id được chọn với status='approved'
    - Nếu trước đó user đang 'pending' thì sẽ được chuyển thành 'approved' nhờ OR REPLACE.
    """
    conn = get_conn()
    cur = conn.cursor()

    # Xoá toàn bộ VĐV đã duyệt của giải
    cur.execute(
        """
        DELETE FROM tournament_players
        WHERE tournament_id = ? AND status = 'approved'
        """,
        (tournament_id,),
    )

    # Chèn lại danh sách approved
    for uid in user_ids:
        cur.execute(
            """
            INSERT OR REPLACE INTO tournament_players
                (tournament_id, user_id, status)
            VALUES (?, ?, 'approved')
            """,
            (tournament_id, uid),
        )

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
    st.markdown(
        "<h3 style='text-align: center; margin-bottom: 20px;'>Đăng nhập / Đăng ký</h3>",
        unsafe_allow_html=True,
    )
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        tab_login, tab_register = st.tabs(["Đăng nhập", "Đăng ký"])

        # TAB ĐĂNG NHẬP
        with tab_login:
            st.write(" ")
            username = st.text_input(
                "Tên đăng nhập",
                key="login_username",
            )
            password = st.text_input(
                "Mật khẩu",
                type="password",
                key="login_password",
            )
            if st.button(
                "Đăng nhập",
                type="primary",
                use_container_width=True,
                key="login_button",
            ):
                user, err = login(username, password)
                if err:
                    st.error(err)
                else:
                    token = create_session_token(user["id"])
                    st.session_state["user"] = dict(user)
                    st.session_state["login_token"] = token
                    st.success(f"Xin chào {user['full_name']}!")
                    st.rerun()

        # TAB ĐĂNG KÝ
        with tab_register:
            st.write(" ")
            full_name = st.text_input(
                "Họ tên",
                key="register_full_name",
            )
            age = st.number_input(
                "Tuổi",
                min_value=5,
                max_value=100,
                value=30,
                step=1,
                key="register_age",
            )
            username_r = st.text_input(
                "Tên đăng nhập mới",
                key="register_username",
            )
            password_r = st.text_input(
                "Mật khẩu mới",
                type="password",
                key="register_password",
            )
            if st.button(
                "Đăng ký tài khoản mới",
                use_container_width=True,
                key="register_button",
            ):
                if not (full_name and username_r and password_r):
                    st.warning("Nhập đủ thông tin")
                else:
                    conn = get_conn()
                    cur = conn.cursor()
                    try:
                        cur.execute(
                            """
                            INSERT INTO users (
                                username, password_hash, full_name, age,
                                role, is_approved, created_at
                            )
                            VALUES (?, ?, ?, ?, 'player', 0, ?)
                            """,
                            (
                                username_r,
                                hash_password(password_r),
                                full_name,
                                age,
                                datetime.utcnow().isoformat(),
                            ),
                        )
                        conn.commit()
                        st.success("Đăng ký thành công, chờ duyệt.")
                    except sqlite3.IntegrityError:
                        st.error("Username đã tồn tại.")
                    finally:
                        conn.close()

def ui_member_management():
    require_role(["is_admin", "is_btc"])
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
                gender_new = st.selectbox(
                    "Giới tính",
                    ["Nam", "Nữ"],
                    index=0,
                    key="add_gender",
                )
            with col2:
                username_new = st.text_input("Username đăng nhập", key="add_username")
                password_new = st.text_input(
                    "Mật khẩu", type="password", key="add_password"
                )
                unit_new = st.text_input("Đơn vị", key="add_unit")

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
                    st.warning("Nhập đủ họ tên, username, mật khẩu.")
                else:
                    conn = get_conn()
                    cur = conn.cursor()
                    try:
                        cur.execute("""
                            INSERT INTO users (
                                username, password_hash, full_name, age,
                                role, is_approved, is_btc, is_admin,
                                gender, unit, created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            username_new,
                            hash_password(password_new),
                            full_name_new,
                            age_new,
                            "player",
                            1 if auto_approve_new else 0,
                            1 if is_btc_new else 0,
                            1 if is_admin_new else 0,
                            gender_new,
                            unit_new,
                            datetime.utcnow().isoformat(),
                        ))
                        conn.commit()
                        st.success("Thêm thành viên thành công.")
                    except sqlite3.IntegrityError:
                        st.error("Username đã tồn tại.")
                    finally:
                        conn.close()


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
                    new_role = "is_admin"
                elif ni_btc:
                    new_role = "is_btc"
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

def ui_btc_ranking_edit():
    """
    Trang riêng để Ban tổ chức chỉnh BXH BTC
    - Có 4 nút: mũi tên đôi (±3 bậc), mũi tên đơn (±1 bậc)
    """
    require_role(["is_admin", "is_btc"])

    st.markdown("### ✏️ Chỉnh sửa BXH do Ban tổ chức")
    st.caption(
        "Dùng các nút ở cuối mỗi dòng để di chuyển VĐV: "
        "⏫ / ⏬ = lên/xuống 3 bậc, ▲ / ▼ = lên/xuống 1 bậc."
    )

    # --- Nút quay lại trang BXH / khởi tạo lại ---
    c_back, c_reset = st.columns([1, 1])
    with c_back:
        if st.button("⬅ Quay lại xem BXH", use_container_width=True, key="btc_back"):
            st.session_state["btc_edit_mode"] = False
            st.session_state.pop("btc_edit_order", None)
            st.rerun()

    players = get_all_players(only_approved=True)
    if not players:
        st.info("Chưa có thành viên nào để xếp hạng.")
        return

    btc_rank = get_btc_ranking()
    hnpr = compute_hnpr()

    def build_default_btc_order():
        # Nếu đã có BXH BTC -> dùng thứ tự hiện tại
        if btc_rank:
            base_ids = [r["ranked_user_id"] for r in btc_rank]
        else:
            # Chưa có: ưu tiên theo HNPR, sau đó bổ sung theo ABC
            if hnpr:
                base_ids = [r["user_id"] for r in hnpr]
            else:
                base_ids = []

        base_set = set(base_ids)
        others = [p for p in players if p["id"] not in base_set]
        others_sorted = sorted(others, key=lambda p: p["full_name"])
        base_ids.extend([p["id"] for p in others_sorted])
        return base_ids

    with c_reset:
        if st.button(
            "🔄 Khởi tạo lại từ HNPR / ABC",
            use_container_width=True,
            key="btc_reset",
        ):
            st.session_state["btc_edit_order"] = build_default_btc_order()
            st.success("Đã khởi tạo lại danh sách BXH BTC theo HNPR/ABC.")
            st.rerun()

    # Khởi tạo state thứ tự
    if "btc_edit_order" not in st.session_state:
        st.session_state["btc_edit_order"] = build_default_btc_order()

    order = st.session_state["btc_edit_order"]
    id_to_name = {p["id"]: p["full_name"] for p in players}

    # Loại ID không còn tồn tại
    order = [uid for uid in order if uid in id_to_name]
    st.session_state["btc_edit_order"] = order

    st.markdown("#### Danh sách xếp hạng hiện tại")

    # Để tránh sửa list khi đang iterate, gom action lại
    action = None  # (index, offset)

    for idx, uid in enumerate(order):
        name = id_to_name.get(uid, f"ID {uid}")
        col1, col2, col3 = st.columns([0.1, 0.6, 0.3])

        with col1:
            st.markdown(f"**{idx + 1}**")

        with col2:
            st.write(name)

        with col3:
            c1, c2, c3, c4 = st.columns(4)
            # ⏫: lên 3 bậc
            if c1.button("⏫", key=f"btc_up3_{uid}"):
                action = (idx, -3)
            # ▲: lên 1 bậc
            if c2.button("▲", key=f"btc_up1_{uid}"):
                action = (idx, -1)
            # ▼: xuống 1 bậc
            if c3.button("▼", key=f"btc_down1_{uid}"):
                action = (idx, +1)
            # ⏬: xuống 3 bậc
            if c4.button("⏬", key=f"btc_down3_{uid}"):
                action = (idx, +3)

    # Thực hiện di chuyển sau khi biết nút nào được bấm
    if action is not None:
        idx, offset = action
        new_idx = max(0, min(len(order) - 1, idx + offset))
        if new_idx != idx:
            new_order = list(order)
            item = new_order.pop(idx)
            new_order.insert(new_idx, item)
            st.session_state["btc_edit_order"] = new_order
        st.rerun()

    st.markdown("---")
    c_save, c_delete = st.columns([2, 1])

    # Nút Lưu BXH
    with c_save:
        if st.button(
            "💾 Lưu BXH BTC",
            type="primary",
            use_container_width=True,
            key="btc_save",
        ):
            current_order = st.session_state.get("btc_edit_order", [])
            if not current_order:
                st.warning("Danh sách hiện tại đang trống, không thể lưu.")
            else:
                save_btc_ranking(current_order)
                st.success("Đã lưu BXH BTC.")
                st.session_state["btc_edit_mode"] = False
                st.session_state.pop("btc_edit_order", None)
                st.rerun()

    # Nút Xoá BXH
    with c_delete:
        if st.button(
            "🗑 Xoá BXH BTC",
            use_container_width=True,
            key="btc_delete",
        ):
            delete_btc_ranking()
            st.session_state.pop("btc_edit_order", None)
            st.success("Đã xoá toàn bộ BXH BTC.")
            # Sau khi xoá thì quay lại trang xem BXH
            st.session_state["btc_edit_mode"] = False
            st.rerun()

def ui_hnpr_page():
    hnpr = compute_hnpr()
    btc_rank = get_btc_ranking()

    user = st.session_state.get("user")

    is_admin = bool(user and user.get("is_admin"))
    is_btc = bool(user and user.get("is_btc"))
    can_edit_btc = is_admin or is_btc


    # Nếu đang ở chế độ chỉnh sửa BXH BTC
    if can_edit_btc and st.session_state.get("btc_edit_mode", False):
        ui_btc_ranking_edit()
        return

    col_left, col_right = st.columns(2)

    # HNPR
    with col_left:
        st.markdown("#### BXH HNPR (do thành viên bình chọn)")
        if not hnpr:
            st.info("Chưa có đủ dữ liệu để tính HNPR.")
        else:
            rows = []
            for r in hnpr:
                rows.append(
                    {
                        "Thứ hạng": r["rank"],
                        "Tên VĐV": r["full_name"],
                        "HNPR (vị trí TB)": round(r["avg_pos"], 2),
                        "Số phiếu": r["vote_count"],
                    }
                )
            st.dataframe(
                rows,
                hide_index=True,
                use_container_width=True,
                height=500,
            )

    # BXH BTC
    with col_right:
        st.markdown("#### BXH do Ban tổ chức thiết lập")
        if not btc_rank:
            st.info("Chưa có BXH BTC.")
        else:
            rows = []
            for r in btc_rank:
                rows.append(
                    {
                        "Thứ hạng": r["position"],
                        "Tên VĐV": r["full_name"],
                    }
                )
            st.dataframe(
                rows,
                hide_index=True,
                use_container_width=True,
                height=500,
            )

    if not can_edit_btc:
        return

    st.markdown("---")
    if st.button("✏️ Quản lý BXH Ban Tổ chức", type="primary", key="btc_edit_btn"):
        st.session_state["btc_edit_mode"] = True
        st.session_state.pop("btc_edit_order", None)
        st.rerun()

def ui_home():
    user = st.session_state.get("user")

    st.subheader("Các giải đang diễn ra 🔥")
    active_ts = get_active_tournaments()
    if not active_ts:
        st.info("Chưa có giải đấu nào.")
        return

    for t in active_ts:
        with st.container():
            # Thẻ giải đấu
            st.markdown(
                f"""
                <div class="tournament-card">
                    <div class="t-title">{t['name']}</div>
                """,
                unsafe_allow_html=True,
            )

            # Kiểu thi đấu & phân bảng
            ctype = (
                t["competition_type"]
                if "competition_type" in t.keys()
                and t["competition_type"] in ("pair", "team")
                else "pair"
            )
            use_pools = bool(t["use_pools"]) if "use_pools" in t.keys() else False

            # Thông tin cơ bản
            st.markdown(
                f"""
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">📍 Địa điểm</span>
                        <span class="info-value">{t['location'] or 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">🗓️ Thời gian</span>
                        <span class="info-value">{t['start_date']} - {t['end_date']}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">🎾 Thể loại</span>
                        <span class="info-value">{'Theo cặp' if ctype == 'pair' else 'Theo đội'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">📊 Phân bảng</span>
                        <span class="info-value">{'Có' if use_pools else 'Không'}</span>
                    </div>
                </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            # ========= ĐĂNG KÝ THAM GIA GIẢI =========
            if user:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT status
                    FROM tournament_players
                    WHERE tournament_id = ? AND user_id = ?
                    """,
                    (t["id"], user["id"]),
                )
                row = cur.fetchone()
                conn.close()

                if row:
                    status = row["status"]
                    if status == "approved":
                        st.success("✅ Bạn đã được BTC duyệt tham gia giải này.")
                    elif status == "pending":
                        st.info("⏳ Bạn đã đăng ký, đang chờ BTC phê duyệt.")
                    else:
                        st.info(f"Trạng thái đăng ký hiện tại: {status}")
                else:
                    if st.button(
                        "Đăng ký tham gia",
                        type="primary",
                        key=f"join_tour_{t['id']}",
                    ):
                        conn = get_conn()
                        cur = conn.cursor()
                        cur.execute(
                            """
                            INSERT OR IGNORE INTO tournament_players
                                (tournament_id, user_id, status)
                            VALUES (?, ?, 'pending')
                            """,
                            (t["id"], user["id"]),
                        )
                        conn.commit()
                        conn.close()
                        st.success("Đã gửi đăng ký, vui lòng chờ BTC phê duyệt.")
                        st.rerun()
            else:
                st.caption("Đăng nhập để đăng ký tham gia giải.")

            st.write("")

            # ========= TABS CHỨC NĂNG CỦA GIẢI =========
            pair_team_label = "Chia cặp" if ctype == "pair" else "Chia đội"

            if use_pools:
                tabs_list = [
                    "Thành viên",
                    "Phân nhóm",
                    pair_team_label,
                    "Phân bảng",
                    "Lịch & Kết quả",
                    "Xếp hạng",
                ]
            else:
                tabs_list = [
                    "Thành viên",
                    "Phân nhóm",
                    pair_team_label,
                    "Lịch & Kết quả",
                    "Xếp hạng",
                ]

            tab_objs = st.tabs(tabs_list)

            with tab_objs[0]:
                ui_tournament_players_view(t["id"])
            with tab_objs[1]:
                ui_tournament_groups_view(t["id"])
            with tab_objs[2]:
                ui_tournament_pairs_teams_view(t["id"])

            if use_pools:
                with tab_objs[3]:
                    ui_tournament_pools_view(t["id"])
                with tab_objs[4]:
                    ui_tournament_results_view(t["id"])
                with tab_objs[5]:
                    ui_tournament_standings(t["id"])
            else:
                with tab_objs[3]:
                    ui_tournament_results_view(t["id"])
                with tab_objs[4]:
                    ui_tournament_standings(t["id"])

        st.write("")

def ui_profile_page():
    require_login()
    user = st.session_state["user"]
    owner_id = user["id"]

    # Nếu đang chỉnh BXH cá nhân -> sang trang riêng
    if st.session_state.get("personal_edit_mode", False):
        ui_personal_ranking_edit(owner_id)
        return

    st.subheader(f"👤 Trang cá nhân: {user['full_name']}")

    tab_info, tab_rank = st.tabs(["Thông tin cá nhân", "Bảng xếp hạng cá nhân"])

    # ======================
    # TAB 1: BXH CÁ NHÂN
    # ======================
    with tab_rank:
        players = [p for p in get_all_players(only_approved=True) if p["id"] != owner_id]
        existing = get_personal_ranking(owner_id)

        if not players:
            st.info("Chưa có đủ thành viên khác để xếp hạng.")
        else:
            if not existing:
                st.info("Chưa có BXH cá nhân.")
                if st.button(
                    "Tạo BXH tự động",
                    type="primary",
                    key="btn_create_personal_bxh",
                ):
                    hnpr = compute_hnpr()
                    if hnpr:
                        order_ids = [r["user_id"] for r in hnpr if r["user_id"] != owner_id]
                    else:
                        order_ids = [
                            p["id"] for p in sorted(players, key=lambda p: p["full_name"])
                        ]
                    save_personal_ranking(owner_id, order_ids)
                    st.success("Đã tạo BXH cá nhân.")
                    st.rerun()
            else:
                st.markdown("#### BXH cá nhân hiện tại")

                rows = []
                for r in existing:
                    rows.append(
                        {
                            "Thứ hạng": r["position"],
                            "Tên VĐV": r["full_name"],
                        }
                    )
                st.dataframe(
                    rows,
                    hide_index=True,
                    use_container_width=True,
                    height=500,
                )

                st.markdown("---")
                if st.button(
                    "✏️ Sửa BXH cá nhân",
                    type="primary",
                    key="personal_edit_btn",
                ):
                    st.session_state["personal_edit_mode"] = True
                    st.session_state.pop(f"personal_edit_order_{owner_id}", None)
                    st.rerun()

    # ======================
    # TAB 2: THÔNG TIN CÁ NHÂN
    # ======================
    with tab_info:
        st.markdown("### Thông tin cá nhân")

        full_name = st.text_input("Họ và tên", value=user["full_name"])
        age = st.number_input(
            "Tuổi",
            min_value=5,
            max_value=100,
            value=int(user["age"] or 30),
            step=1,
        )

        # NEW: Giới tính + Đơn vị
        current_gender = user.get("gender") or "Nam"
        gender_index = 0 if current_gender == "Nam" else 1
        gender = st.selectbox(
            "Giới tính",
            ["Nam", "Nữ"],
            index=gender_index,
        )
        unit = st.text_input(
            "Đơn vị",
            value=user.get("unit") or "",
        )

        st.markdown("#### Đổi mật khẩu (không bắt buộc)")
        current_pw = st.text_input("Mật khẩu hiện tại", type="password")
        new_pw = st.text_input("Mật khẩu mới", type="password")
        new_pw2 = st.text_input("Nhập lại mật khẩu mới", type="password")

        if st.button("💾 Lưu thông tin cá nhân", type="primary"):
            # Kiểm tra và cập nhật
            conn = get_conn()
            cur = conn.cursor()

            if new_pw or new_pw2:
                # Đổi mật khẩu
                if not current_pw:
                    st.error("Vui lòng nhập mật khẩu hiện tại.")
                else:
                    db_user = get_user_by_id(user["id"])
                    if not verify_password(current_pw, db_user["password_hash"]):
                        st.error("Mật khẩu hiện tại không đúng.")
                    elif new_pw != new_pw2:
                        st.error("Mật khẩu mới nhập lại không khớp.")
                    else:
                        cur.execute(
                            """
                            UPDATE users
                            SET full_name = ?, age = ?, gender = ?, unit = ?, password_hash = ?
                            WHERE id = ?
                            """,
                            (
                                full_name,
                                age,
                                gender,
                                unit,
                                hash_password(new_pw),
                                user["id"],
                            ),
                        )
                        conn.commit()
                        st.success("Đã cập nhật thông tin và mật khẩu.")
                        st.session_state["user"] = dict(get_user_by_id(user["id"]))
            else:
                # Không đổi mật khẩu
                cur.execute(
                    """
                    UPDATE users
                    SET full_name = ?, age = ?, gender = ?, unit = ?
                    WHERE id = ?
                    """,
                    (
                        full_name,
                        age,
                        gender,
                        unit,
                        user["id"],
                    ),
                )
                conn.commit()
                st.success("Đã cập nhật thông tin.")
                st.session_state["user"] = dict(get_user_by_id(user["id"]))

            conn.close()

def ui_personal_ranking_edit(owner_id: int):
    """
    Trang riêng chỉnh sửa BXH cá nhân của 1 người chơi
    - Dùng mũi tên đôi (±3) và mũi tên đơn (±1) giống trang BTC
    """
    require_login()
    user = st.session_state["user"]
    # Chỉ cho chính chủ hoặc admin chỉnh sửa
    is_admin = bool(user.get("is_admin"))
    if user["id"] != owner_id and not is_admin:
        st.error("Bạn không có quyền chỉnh sửa BXH cá nhân này.")
        return

    st.markdown("### ✏️ Chỉnh sửa BXH cá nhân")
    st.caption(
        "Dùng các nút ở cuối mỗi dòng để di chuyển VĐV: "
        "⏫ / ⏬ = lên/xuống 3 bậc, ▲ / ▼ = lên/xuống 1 bậc."
    )

    # Nút quay lại Trang cá nhân + khởi tạo lại
    c_back, c_reset = st.columns([1, 1])
    with c_back:
        if st.button(
            "⬅ Quay lại Trang cá nhân",
            use_container_width=True,
            key="personal_back",
        ):
            st.session_state["personal_edit_mode"] = False
            st.session_state.pop(f"personal_edit_order_{owner_id}", None)
            st.rerun()

    players = [p for p in get_all_players(only_approved=True) if p["id"] != owner_id]
    if not players:
        st.info("Chưa có đủ thành viên khác để xếp hạng.")
        return

    existing = get_personal_ranking(owner_id)
    hnpr = compute_hnpr()

    def build_default_personal_order():
        if existing:
            base_ids = [r["ranked_user_id"] for r in existing]
        else:
            if hnpr:
                base_ids = [r["user_id"] for r in hnpr if r["user_id"] != owner_id]
            else:
                base_ids = []
        base_set = set(base_ids)
        others = [p for p in players if p["id"] not in base_set]
        others_sorted = sorted(others, key=lambda p: p["full_name"])
        base_ids.extend([p["id"] for p in others_sorted])
        return base_ids

    # Khởi tạo lại theo HNPR/ABC
    with c_reset:
        if st.button(
            "🔄 Khởi tạo lại từ HNPR / ABC",
            use_container_width=True,
            key="personal_reset",
        ):
            st.session_state[f"personal_edit_order_{owner_id}"] = (
                build_default_personal_order()
            )
            st.success("Đã khởi tạo lại BXH cá nhân theo HNPR/ABC.")
            st.rerun()

    state_key = f"personal_edit_order_{owner_id}"
    if state_key not in st.session_state:
        st.session_state[state_key] = build_default_personal_order()

    order = st.session_state[state_key]
    id_to_name = {p["id"]: p["full_name"] for p in players}

    # Loại id không còn trong danh sách
    order = [uid for uid in order if uid in id_to_name]
    st.session_state[state_key] = order

    st.markdown("#### Danh sách xếp hạng hiện tại")

    action = None  # (index, offset)

    for idx, uid in enumerate(order):
        name = id_to_name.get(uid, f"ID {uid}")
        col1, col2, col3 = st.columns([0.1, 0.6, 0.3])

        with col1:
            st.markdown(f"**{idx + 1}**")

        with col2:
            st.write(name)

        with col3:
            c1, c2, c3, c4 = st.columns(4)
            # ⏫: lên 3 bậc
            if c1.button("⏫", key=f"personal_up3_{owner_id}_{uid}"):
                action = (idx, -3)
            # ▲: lên 1 bậc
            if c2.button("▲", key=f"personal_up1_{owner_id}_{uid}"):
                action = (idx, -1)
            # ▼: xuống 1 bậc
            if c3.button("▼", key=f"personal_down1_{owner_id}_{uid}"):
                action = (idx, +1)
            # ⏬: xuống 3 bậc
            if c4.button("⏬", key=f"personal_down3_{owner_id}_{uid}"):
                action = (idx, +3)

    if action is not None:
        idx, offset = action
        new_idx = max(0, min(len(order) - 1, idx + offset))
        if new_idx != idx:
            new_order = list(order)
            item = new_order.pop(idx)
            new_order.insert(new_idx, item)
            st.session_state[state_key] = new_order
        st.rerun()

    st.markdown("---")
    c_save, c_delete = st.columns([2, 1])

    # Nút Lưu BXH cá nhân
    with c_save:
        if st.button(
            "💾 Lưu BXH cá nhân",
            type="primary",
            use_container_width=True,
            key="personal_save",
        ):
            current_order = st.session_state.get(state_key, [])
            if not current_order:
                st.warning("Danh sách hiện tại đang trống, không thể lưu.")
            else:
                save_personal_ranking(owner_id, current_order)
                st.success("Đã lưu BXH cá nhân.")
                st.session_state["personal_edit_mode"] = False
                st.session_state.pop(state_key, None)
                st.rerun()

    # Nút Xoá BXH cá nhân
    with c_delete:
        if st.button(
            "🗑 Xoá BXH cá nhân",
            use_container_width=True,
            key="personal_delete",
        ):
            delete_personal_ranking(owner_id)
            st.session_state.pop(state_key, None)
            st.success("Đã xoá toàn bộ BXH cá nhân.")
            st.session_state["personal_edit_mode"] = False
            st.rerun()

def ui_tournament_page():
    require_role(["is_admin", "is_btc"])
    if "tournament_view_mode" not in st.session_state: st.session_state["tournament_view_mode"] = "list"
    if st.session_state["tournament_view_mode"] == "detail" and st.session_state["selected_tournament_id"]:
        ui_tournament_detail_page(st.session_state["selected_tournament_id"])
    else: ui_tournament_list_page()

def ui_tournament_list_page():
    st.subheader("🛠️ Quản lý giải đấu")
    if "show_create_t" not in st.session_state:
        st.session_state["show_create_t"] = False

    tournaments = get_tournaments()
    if tournaments and not st.session_state["show_create_t"]:
        st.markdown(f"**Danh sách giải ({len(tournaments)})**")
        cols = st.columns([0.05, 0.25, 0.15, 0.2, 0.1, 0.15, 0.1])
        cols[0].markdown("**ID**")
        cols[1].markdown("**Tên giải**")
        cols[2].markdown("**Thể loại**")
        cols[3].markdown("**Thời gian**")
        cols[4].markdown("**Active**")
        cols[5].markdown("**Thao tác**")

        st.markdown("---")
        for t in tournaments:
            tid = t["id"]
            # competition_type có thể None
            if "competition_type" in t.keys() and t["competition_type"] in ("pair", "team"):
                ctype = t["competition_type"]
            else:
                ctype = "pair"

            c = st.columns([0.05, 0.25, 0.15, 0.2, 0.1, 0.15, 0.1])
            c[0].write(tid)
            c[1].write(t["name"])
            c[2].write("Cặp" if ctype == "pair" else "Đội")
            c[3].write(f"{t['start_date'] or ''}")
            c[4].markdown("✅" if t["is_active"] else "")

            with c[5]:
                b1, b2, b3 = st.columns(3)
                if b1.button("👁", key=f"v_{tid}"):
                    st.session_state["tournament_view_mode"] = "detail"
                    st.session_state["selected_tournament_id"] = tid
                    st.rerun()
                if b2.button("✏", key=f"e_{tid}"):
                    st.session_state["editing_tournament_id"] = tid
                    st.session_state["show_create_t"] = True
                    st.rerun()
                if b3.button("🗑", key=f"d_{tid}"):
                    delete_tournament(tid)
                    st.rerun()

        st.markdown("---")

    if not st.session_state["show_create_t"]:
        if st.button("➕ Thêm giải mới", type="primary"):
            st.session_state["show_create_t"] = True
            st.rerun()
        return

    # ----- Form tạo / sửa giải -----
    with st.container():
        st.markdown("### 📝 Thông tin giải đấu")
        editing_id = st.session_state.get("editing_tournament_id")

        if editing_id:
            t = get_tournament_by_id(editing_id)
            if t:
                d_name = t["name"]
                d_start = t["start_date"]
                d_end = t["end_date"]
                d_loc = t["location"]
                d_nc = t["num_courts"] or 4
                d_act = bool(t["is_active"])

                # competition_type
                if "competition_type" in t.keys() and t["competition_type"] in ("pair", "team"):
                    d_ctype = t["competition_type"]
                else:
                    d_ctype = "pair"

                # use_pools
                if "use_pools" in t.keys():
                    d_pool = bool(t["use_pools"])
                else:
                    d_pool = True

                # adv_per_pool
                if "adv_per_pool" in t.keys():
                    d_adv = t["adv_per_pool"]
                else:
                    d_adv = None
            else:
                # fallback nếu không tìm thấy giải (hiếm)
                d_name = ""
                d_start = ""
                d_end = ""
                d_loc = ""
                d_nc = 4
                d_act = False
                d_ctype = "pair"
                d_pool = True
                d_adv = None
        else:
            d_name = ""
            d_start = ""
            d_end = ""
            d_loc = ""
            d_nc = 4
            d_act = False
            d_ctype = "pair"
            d_pool = True
            d_adv = None

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
                ctype = st.radio(
                    "Thể loại",
                    ["Theo cặp", "Theo đội"],
                    index=0 if d_ctype == "pair" else 1,
                    horizontal=True,
                )
                use_pools = st.checkbox("Có phân bảng", value=d_pool)
                is_active = st.checkbox("Đang diễn ra", value=d_act)

            st.markdown("---")
            c_s, c_c = st.columns([1, 1])

            if c_s.form_submit_button("💾 Lưu", type="primary", use_container_width=True):
                if not name:
                    st.warning("Nhập tên giải")
                else:
                    upsert_tournament(
                        editing_id,
                        name,
                        start_date,
                        end_date,
                        location,
                        num_courts,
                        is_active,
                        "pair" if ctype == "Theo cặp" else "team",
                        use_pools,
                        d_adv,
                    )
                    st.success("Đã lưu.")
                    st.session_state["editing_tournament_id"] = None
                    st.session_state["show_create_t"] = False
                    st.rerun()

            if c_c.form_submit_button("Huỷ", use_container_width=True):
                st.session_state["editing_tournament_id"] = None
                st.session_state["show_create_t"] = False
                st.rerun()

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
    current = get_tournament_players(t_id)  # chỉ lấy approved
    if current:
        total = len(current)
        num_male = sum(1 for p in current if (p["gender"] or "") == "Nam")
        num_female = sum(1 for p in current if (p["gender"] or "") == "Nữ")

        st.markdown(
            f"Hiện có **{total}** VĐV đã được duyệt tham gia "
            f"(Nam: **{num_male}**, Nữ: **{num_female}**)."
        )
        cols = st.columns(4)
        for i, p in enumerate(current):
            cols[i % 4].markdown(f"👤 {p['full_name']}")
    else:
        st.info("Chưa có VĐV đã được BTC duyệt.")

def ui_tournament_players(t_id):
    user = st.session_state.get("user")
    is_btc_admin = bool(
        user and (user.get("is_admin") or user.get("is_btc"))
    )

    # ----- 1. Danh sách đã được duyệt -----
    approved = get_tournament_players(t_id)  # chỉ approved
    st.markdown("#### 1. Thành viên đã được duyệt tham gia")

    if approved:
        total = len(approved)
        num_male = sum(1 for p in approved if (p["gender"] or "") == "Nam")
        num_female = sum(1 for p in approved if (p["gender"] or "") == "Nữ")

        st.markdown(
            f"Hiện có **{total}** VĐV đã được duyệt tham gia "
            f"(Nam: **{num_male}**, Nữ: **{num_female}**)."
        )
        with st.expander("Xem danh sách chi tiết"):
            cols = st.columns(4)
            for i, p in enumerate(approved):
                cols[i % 4].write(f"- {p['full_name']}")
    else:
        st.info("Chưa có VĐV nào được duyệt.")

    # Chỉ BTC / admin mới được cấu hình danh sách approved
    if is_btc_admin:
        flag_key = f"show_add_players_{t_id}"
        if flag_key not in st.session_state:
            st.session_state[flag_key] = False

        if not st.session_state[flag_key]:
            if st.button("➕ Thêm / Sửa danh sách đã duyệt", key=f"btn_add_{t_id}"):
                st.session_state[flag_key] = True
                st.rerun()
        else:
            if st.button("⬅ Đóng phần Thêm / Sửa", key=f"btn_hide_{t_id}"):
                st.session_state[flag_key] = False
                st.rerun()

            st.write("Chọn thành viên sẽ được coi là **đã duyệt tham gia**:")

            all_p = get_all_players(only_approved=True)
            current_ids = {p["user_id"] for p in approved}
            selected_ids = set(current_ids)

            with st.form(f"p_form_{t_id}"):
                cols = st.columns(4)
                for i, p in enumerate(all_p):
                    checked = cols[i % 4].checkbox(
                        p["full_name"],
                        value=p["id"] in current_ids,
                        key=f"chk_{t_id}_{p['id']}",
                    )
                    if checked:
                        selected_ids.add(p["id"])
                    else:
                        selected_ids.discard(p["id"])

                if st.form_submit_button("💾 Lưu danh sách đã duyệt", type="primary"):
                    set_tournament_players(t_id, list(selected_ids))
                    st.success("Đã cập nhật danh sách VĐV được duyệt.")
                    st.session_state[flag_key] = False
                    st.rerun()

    st.markdown("---")

    # ----- 2. Danh sách chờ duyệt -----
    st.markdown("#### 2. Đăng ký chờ BTC phê duyệt")

    pending = get_tournament_pending_players(t_id)

    if not pending:
        st.info("Hiện không có đăng ký nào đang chờ duyệt.")
        return

    if not is_btc_admin:
        st.info("Chỉ BTC / Admin mới được duyệt danh sách này.")
        # Vẫn hiển thị tên cho minh bạch
        cols = st.columns(4)
        for i, p in enumerate(pending):
            cols[i % 4].write(f"- {p['full_name']}")
        return

    # BTC / admin: có quyền duyệt / từ chối
    for p in pending:
        uid = p["user_id"]
        full_name = p["full_name"]

        c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
        with c1:
            st.write(f"👤 {full_name}")
        with c2:
            if st.button("✅ Duyệt", key=f"approve_{t_id}_{uid}"):
                conn = get_conn()
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE tournament_players
                    SET status = 'approved'
                    WHERE tournament_id = ? AND user_id = ?
                    """,
                    (t_id, uid),
                )
                conn.commit()
                conn.close()
                st.success(f"Đã duyệt: {full_name}")
                st.rerun()
        with c3:
            if st.button("❌ Từ chối", key=f"reject_{t_id}_{uid}"):
                conn = get_conn()
                cur = conn.cursor()
                # Từ chối: xoá hẳn bản ghi pending
                cur.execute(
                    """
                    DELETE FROM tournament_players
                    WHERE tournament_id = ? AND user_id = ?
                    """,
                    (t_id, uid),
                )
                conn.commit()
                conn.close()
                st.warning(f"Đã từ chối: {full_name}")
                st.rerun()

def ui_tournament_groups_view(t_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            tp.user_id,
            tp.group_name,
            u.full_name
        FROM tournament_players tp
        JOIN users u ON u.id = tp.user_id
        WHERE tp.tournament_id = ? AND tp.status = 'approved'
        ORDER BY tp.group_name, u.full_name
        """,
        (t_id,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        st.info("Chưa phân nhóm (hoặc chưa có VĐV được duyệt).")
        return

    g_map = {}
    for r in rows:
        g_name = r["group_name"] or "N/A"
        g_map.setdefault(g_name, []).append(r["full_name"])

    cols = st.columns(len(g_map) if g_map else 1)
    for i, (g, names) in enumerate(sorted(g_map.items())):
        with cols[i % len(cols)]:
            st.info(f"**Nhóm {g}** ({len(names)})")
            for n in names:
                st.markdown(f"• {n}")

def ui_tournament_groups(t_id):
    players = get_tournament_players(t_id)
    if not players:
        st.warning("Thêm thành viên trước.")
        return

    st.markdown("#### Cấu hình phân nhóm")

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
        # ====== KIỂM TRA CẤU HÌNH NHÓM (ĐỐI XỨNG + TỔNG) ======
        total_players = len(players)
        sizes = [size for _, size in g_defs]
        total_cfg = sum(sizes)

        # 1) Tổng số VĐV trong các nhóm phải đúng với tổng tham gia
        if total_cfg != total_players:
            st.error(
                f"Tổng số VĐV trong cấu hình nhóm là {total_cfg}, "
                f"nhưng tổng số thành viên tham gia là {total_players}. "
                "Vui lòng điều chỉnh lại số lượng từng nhóm cho khớp."
            )
            return

        # 2) Đối xứng: Nhóm 1 = Nhóm N, Nhóm 2 = Nhóm N-1, ...
        n = len(sizes)
        for i in range(n // 2):
            left = sizes[i]
            right = sizes[n - 1 - i]
            if left != right:
                st.error(
                    f"Số lượng Nhóm {i+1} ({left}) phải bằng Nhóm {n - i} ({right}). "
                    "Vui lòng điều chỉnh lại cho đối xứng."
                )
                return
        # Trung tâm (n lẻ) không cần bằng ai, chỉ cần tổng đúng là được.

        # ====== PHÂN NHÓM SAU KHI CẤU HÌNH HỢP LỆ ======
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
                "UPDATE tournament_players SET group_name = ? "
                "WHERE tournament_id = ? AND user_id = ?",
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
    t = get_tournament_by_id(t_id)
    ctype = t["competition_type"] if "competition_type" in t.keys() else "pair"
    comps = get_competitors(t_id)
    m_map = get_competitor_members_map(t_id)

    if not comps:
        st.info("Chưa có danh sách thi đấu.")
        return

    # THI ĐẤU THEO ĐỘI -> hiển thị giống tab "Phân nhóm"
    if ctype == "team":
        st.markdown("### 🏅 Danh sách các đội")

        num_cols = 4 if len(comps) >= 4 else len(comps)
        cols = st.columns(num_cols if num_cols > 0 else 1)

        for i, c in enumerate(comps):
            members = [m[1] for m in m_map.get(c["id"], [])]

            with cols[i % num_cols]:
                # Giống kiểu Nhóm A/B ở tab phân nhóm
                st.info(f"**{c['name']}** ({len(members)} VĐV)")
                for n in members:
                    st.markdown(f"• {n}")

    # THI ĐẤU THEO CẶP -> giữ nguyên layout lưới cũ
    else:
        st.markdown("### 🎾 Danh sách cặp đấu")
        cols = st.columns(3)
        for i, c in enumerate(comps):
            with cols[i % 3]:
                st.success(f"{build_competitor_display_name(c['id'], m_map)}")

def ui_tournament_pairs_teams(t_id):
    t = get_tournament_by_id(t_id); ctype = t["competition_type"] if "competition_type" in t.keys() else "pair"
    st.markdown(f"#### Tạo {'Cặp' if ctype == 'pair' else 'Đội'} thi đấu")
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
    st.markdown("#### Phân bảng")
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

    user = st.session_state["user"]

    # --- HEADER ---
    c_logo, c_title, c_user = st.columns([0.8, 7, 2])

    c_logo.markdown(
        "<div style='font-size:2.5rem; text-align:center;'>🏓</div>",
        unsafe_allow_html=True
    )

    c_title.markdown(
        "<h1 style='margin:0; font-size: 1.8rem; padding-top:5px; color:#111827;'>HNX Pickleball Allstars</h1>",
        unsafe_allow_html=True
    )

    # Góc phải: Hi username + Logout
    if user:
        with c_user:
            c1, c2 = st.columns([0.5, 0.5])
            with c1:
                st.markdown(
                    f"<div style='text-align:right; padding-top:15px; font-size:0.9rem; vertical-align: middle;'>Hi, <b>{user['full_name']}</b></div>",
                    unsafe_allow_html=True
                )
            with c2:
                if st.button("Đăng xuất", key="logout_btn", help="Đăng xuất", use_container_width=True):
                    st.session_state.clear()
                    st.rerun()
    else:
        c_user.write("")

    # --- MENU CHÍNH ---
    tabs_list = ["Trang chủ", "Bảng xếp hạng"]

    if not user:
        tabs_list.append("Đăng nhập")
    else:
        if user.get("is_admin") or user.get("is_btc"):
            tabs_list.extend(["Thành viên", "Giải đấu"])
        tabs_list.append("Cá nhân")

    st.markdown('<div class="main-menu-tabs">', unsafe_allow_html=True)
    selected_tabs = st.tabs(tabs_list)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- TABS RENDER ---
    with selected_tabs[0]:
        ui_home()

    with selected_tabs[1]:
        ui_hnpr_page()

    if not user:
        with selected_tabs[2]:
            ui_login_register()
    else:
        idx = 2
        if user.get("is_admin") or user.get("is_btc"):
            with selected_tabs[idx]:
                ui_member_management()
            with selected_tabs[idx + 1]:
                ui_tournament_page()
            idx += 2

        with selected_tabs[idx]:
            ui_profile_page()
    
if __name__ == "__main__":
    main()