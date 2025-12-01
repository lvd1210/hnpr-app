import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "hnx_pickball_allstars.db"

# ------------------ DB helpers ------------------ #

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

        # Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER,
            role TEXT NOT NULL DEFAULT 'player', -- vẫn giữ để tương thích
            is_approved INTEGER NOT NULL DEFAULT 0,
            is_btc INTEGER NOT NULL DEFAULT 0,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)


    # Tournaments
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

    # Tournament players
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tournament_players (
            tournament_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'approved', -- approved / pending
            group_name TEXT,
            PRIMARY KEY (tournament_id, user_id)
        )
    """)

    # Personal rankings (each owner ranks others)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS personal_ranking_items (
            owner_id INTEGER NOT NULL,
            ranked_user_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            PRIMARY KEY (owner_id, ranked_user_id)
        )
    """)

    # Competitors (pair or team)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            kind TEXT NOT NULL, -- pair / team
            pool_name TEXT
        )
    """)

    # Members of a competitor
    cur.execute("""
        CREATE TABLE IF NOT EXISTS competitor_members (
            competitor_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (competitor_id, user_id)
        )
    """)

    # Matches
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

    conn.commit()

    # Create default admin if not exists
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        password_hash = hash_password("admin")
        cur.execute("""
            INSERT INTO users (username, password_hash, full_name, age, role, is_approved, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("admin", password_hash, "Administrator", 0, "admin", 1, datetime.utcnow().isoformat()))
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
    if not user:
        return None, "Không tìm thấy tài khoản"
    if not verify_password(password, user["password_hash"]):
        return None, "Sai mật khẩu"
    if not user["is_approved"]:
        return None, "Tài khoản chưa được phê duyệt bởi Admin/BTC"
    return user, None

def require_login():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.warning("Bạn cần đăng nhập để sử dụng chức năng này.")
        st.stop()

def require_role(roles):
    """
    roles: ví dụ ["admin", "btc"]
    Quy ước:
    - admin: cần is_admin = 1
    - btc: cần is_btc = 1 hoặc is_admin = 1
    - player: chỉ cần đăng nhập
    """
    require_login()
    u = st.session_state["user"]

    is_admin = bool(u.get("is_admin", 0))
    is_btc = bool(u.get("is_btc", 0))

    ok = False

    if "admin" in roles and is_admin:
        ok = True
    if "btc" in roles and (is_btc or is_admin):
        ok = True
    if "player" in roles:
        ok = True

    if not ok:
        st.warning("Bạn không có quyền truy cập chức năng này.")
        st.stop()

# ------------------ HNPR logic ------------------ #

def get_all_players(only_approved=True):
    conn = get_conn()
    cur = conn.cursor()
    if only_approved:
        cur.execute("SELECT * FROM users WHERE role = 'player' AND is_approved = 1 ORDER BY full_name")
    else:
        cur.execute("SELECT * FROM users ORDER BY full_name")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_personal_ranking(owner_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT pri.ranked_user_id, pri.position, u.full_name
        FROM personal_ranking_items pri
        JOIN users u ON u.id = pri.ranked_user_id
        WHERE pri.owner_id = ?
        ORDER BY pri.position ASC
    """, (owner_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def save_personal_ranking(owner_id, ordered_ids):
    conn = get_conn()
    cur = conn.cursor()
    # clear old
    cur.execute("DELETE FROM personal_ranking_items WHERE owner_id = ?", (owner_id,))
    # insert new
    for pos, uid in enumerate(ordered_ids, start=1):
        cur.execute("""
            INSERT INTO personal_ranking_items (owner_id, ranked_user_id, position)
            VALUES (?, ?, ?)
        """, (owner_id, uid, pos))
    conn.commit()
    conn.close()

def delete_personal_ranking(owner_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM personal_ranking_items WHERE owner_id = ?", (owner_id,))
    conn.commit()
    conn.close()

def compute_hnpr():
    """
    Tính HNPR dựa trên trung bình vị trí của từng VĐV trong các bảng xếp hạng cá nhân.
    Vị trí trung bình càng nhỏ thì xếp hạng càng cao.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT ranked_user_id,
               AVG(position) AS avg_pos,
               COUNT(DISTINCT owner_id) AS vote_count
        FROM personal_ranking_items
        GROUP BY ranked_user_id
        HAVING vote_count > 0
        ORDER BY avg_pos ASC
    """)
    rows = cur.fetchall()
    result = []
    rank = 1
    for r in rows:
        user = get_user_by_id(r["ranked_user_id"])
        if not user:
            continue
        result.append({
            "rank": rank,
            "user_id": r["ranked_user_id"],
            "full_name": user["full_name"],
            "avg_pos": r["avg_pos"],
            "vote_count": r["vote_count"],
        })
        rank += 1
    conn.close()
    return result

def get_hnpr_order_or_alpha():
    ranking = compute_hnpr()
    if ranking:
        return [r["user_id"] for r in ranking]
    else:
        return [p["id"] for p in get_all_players(only_approved=True)]

# ------------------ Tournament helpers ------------------ #

def get_tournaments():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tournaments ORDER BY id DESC")
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

def upsert_tournament(t_id, name, start_date, end_date, location, num_courts, is_active):
    conn = get_conn()
    cur = conn.cursor()
    if t_id is None:
        cur.execute("""
            INSERT INTO tournaments (name, start_date, end_date, location, num_courts, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, start_date, end_date, location, num_courts, 1 if is_active else 0))
        t_id = cur.lastrowid
    else:
        cur.execute("""
            UPDATE tournaments
            SET name = ?, start_date = ?, end_date = ?, location = ?, num_courts = ?, is_active = ?
            WHERE id = ?
        """, (name, start_date, end_date, location, num_courts, 1 if is_active else 0, t_id))
    # only one active at a time
    if is_active:
        cur.execute("UPDATE tournaments SET is_active = CASE WHEN id = ? THEN 1 ELSE 0 END", (t_id,))
    conn.commit()
    conn.close()
    return t_id

def delete_tournament(t_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tournament_players WHERE tournament_id = ?", (t_id,))
    cur.execute("DELETE FROM competitors WHERE tournament_id = ?", (t_id,))
    cur.execute("DELETE FROM matches WHERE tournament_id = ?", (t_id,))
    cur.execute("DELETE FROM tournaments WHERE id = ?", (t_id,))
    conn.commit()
    conn.close()

def get_tournament_players(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT tp.tournament_id, tp.user_id, tp.status, tp.group_name, u.full_name
        FROM tournament_players tp
        JOIN users u ON u.id = tp.user_id
        WHERE tp.tournament_id = ?
        ORDER BY u.full_name
    """, (tournament_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def set_tournament_players(tournament_id, user_ids):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tournament_players WHERE tournament_id = ?", (tournament_id,))
    for uid in user_ids:
        cur.execute("""
            INSERT INTO tournament_players (tournament_id, user_id, status)
            VALUES (?, ?, 'approved')
        """, (tournament_id, uid))
    conn.commit()
    conn.close()

def get_tournament_active():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tournaments WHERE is_active = 1 LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row

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
    if comp_ids:
        cur.executemany("DELETE FROM competitor_members WHERE competitor_id = ?", [(cid,) for cid in comp_ids])
    cur.execute("DELETE FROM matches WHERE tournament_id = ?", (tournament_id,))
    cur.execute("DELETE FROM competitors WHERE tournament_id = ?", (tournament_id,))
    conn.commit()
    conn.close()

def create_competitor(conn, tournament_id, name, kind, member_ids):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO competitors (tournament_id, name, kind)
        VALUES (?, ?, ?)
    """, (tournament_id, name, kind))
    comp_id = cur.lastrowid
    for uid in member_ids:
        cur.execute("""
            INSERT INTO competitor_members (competitor_id, user_id)
            VALUES (?, ?)
        """, (comp_id, uid))
    return comp_id

def get_competitor_members_map(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id AS competitor_id, u.id AS user_id, u.full_name
        FROM competitors c
        JOIN competitor_members cm ON cm.competitor_id = c.id
        JOIN users u ON u.id = cm.user_id
        WHERE c.tournament_id = ?
        ORDER BY c.id, u.full_name
    """, (tournament_id,))
    rows = cur.fetchall()
    conn.close()
    comp_members = {}
    for r in rows:
        comp_members.setdefault(r["competitor_id"], []).append((r["user_id"], r["full_name"]))
    return comp_members

def get_matches(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.*, c1.name AS name1, c2.name AS name2
        FROM matches m
        JOIN competitors c1 ON c1.id = m.competitor1_id
        JOIN competitors c2 ON c2.id = m.competitor2_id
        WHERE m.tournament_id = ?
        ORDER BY m.id
    """, (tournament_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_match(tournament_id, comp1_id, comp2_id, score1, score2, reporter_id, auto_confirm=True):
    if score1 == score2:
        st.warning("Hiện tại hệ thống chưa hỗ trợ hoà, vui lòng nhập tỉ số có đội thắng.")
        return
    winner_id = comp1_id if score1 > score2 else comp2_id
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO matches (tournament_id, competitor1_id, competitor2_id, score1, score2, winner_id, reported_by, confirmed_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (tournament_id, comp1_id, comp2_id, score1, score2, winner_id, reporter_id, reporter_id if auto_confirm else None))
    conn.commit()
    conn.close()

def compute_standings(tournament_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.name
        FROM competitors c
        WHERE c.tournament_id = ?
    """, (tournament_id,))
    competitors = {r["id"]: {"name": r["name"], "wins": 0, "pts_for": 0, "pts_against": 0} for r in cur.fetchall()}

    cur.execute("""
        SELECT * FROM matches
        WHERE tournament_id = ? AND (confirmed_by IS NOT NULL)
    """, (tournament_id,))
    for m in cur.fetchall():
        c1 = m["competitor1_id"]
        c2 = m["competitor2_id"]
        s1 = m["score1"]
        s2 = m["score2"]
        competitors[c1]["pts_for"] += s1
        competitors[c1]["pts_against"] += s2
        competitors[c2]["pts_for"] += s2
        competitors[c2]["pts_against"] += s1
        if m["winner_id"] == c1:
            competitors[c1]["wins"] += 1
        elif m["winner_id"] == c2:
            competitors[c2]["wins"] += 1

    conn.close()

    table = []
    for cid, info in competitors.items():
        diff = info["pts_for"] - info["pts_against"]
        table.append({
            "id": cid,
            "name": info["name"],
            "wins": info["wins"],
            "pts_for": info["pts_for"],
            "pts_against": info["pts_against"],
            "diff": diff,
        })

    table.sort(key=lambda x: (-x["wins"], -x["diff"], x["name"]))
    return table

# ------------------ UI sections ------------------ #

def ui_login_register():
    st.subheader("Đăng nhập / Đăng ký")

    tab_login, tab_register = st.tabs(["Đăng nhập", "Đăng ký"])

    with tab_login:
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập"):
            user, err = login(username, password)
            if err:
                st.error(err)
            else:
                st.session_state["user"] = dict(user)
                st.success(f"Xin chào {user['full_name']}!")
                st.rerun()


    with tab_register:
        full_name = st.text_input("Họ tên")
        age = st.number_input("Tuổi", min_value=5, max_value=100, value=30, step=1)
        username_r = st.text_input("Tên đăng nhập mới")
        password_r = st.text_input("Mật khẩu mới", type="password")
        if st.button("Đăng ký tài khoản mới"):
            if not (full_name and username_r and password_r):
                st.warning("Vui lòng nhập đầy đủ thông tin.")
            else:
                conn = get_conn()
                cur = conn.cursor()
                try:
                    cur.execute("""
                        INSERT INTO users (username, password_hash, full_name, age, role, is_approved, created_at)
                        VALUES (?, ?, ?, ?, 'player', 0, ?)
                    """, (username_r, hash_password(password_r), full_name, age, datetime.utcnow().isoformat()))
                    conn.commit()
                    st.success("Đăng ký thành công, vui lòng chờ Admin/BTC phê duyệt.")
                except sqlite3.IntegrityError:
                    st.error("Tên đăng nhập đã tồn tại.")
                finally:
                    conn.close()

def ui_member_management():
    require_role(["admin", "btc"])
    st.subheader("Quản lý thành viên")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, full_name, age, role, is_approved, is_btc, is_admin FROM users ORDER BY created_at DESC")
    users = cur.fetchall()

    if not users:
        st.info("Chưa có thành viên nào.")
        conn.close()
        return

    st.markdown("### Danh sách thành viên")

    with st.form("members_form"):
        # Header
        header_cols = st.columns([0.05, 0.15, 0.25, 0.1, 0.15, 0.15, 0.1])
        header_cols[0].write("ID")
        header_cols[1].write("Username")
        header_cols[2].write("Họ tên")
        header_cols[3].write("Tuổi")
        header_cols[4].write("Ban tổ chức")
        header_cols[5].write("Admin")
        header_cols[6].write("Duyệt")

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

            cols = st.columns([0.05, 0.15, 0.25, 0.1, 0.15, 0.15, 0.1])

            cols[0].write(uid)
            cols[1].write(username)
            cols[2].write(full_name)
            cols[3].write(age if age is not None else "")

            # Checkbox BTC (mặc định theo is_btc)
            btc_key = f"btc_{uid}"
            btc_checked = cols[4].checkbox(
                "",
                value=bool(is_btc),
                key=btc_key,
                label_visibility="collapsed",
            )

            # Checkbox Admin (mặc định theo is_admin)
            admin_key = f"admin_{uid}"
            admin_checked = cols[5].checkbox(
                "",
                value=bool(is_admin),
                key=admin_key,
                label_visibility="collapsed",
            )

            new_is_btc[uid] = 1 if btc_checked else 0
            new_is_admin[uid] = 1 if admin_checked else 0

            # Cột duyệt
            if not is_approved:
                approve_key = f"approve_{uid}"
                approve_checked = cols[6].checkbox(
                    "",
                    key=approve_key,
                    label_visibility="collapsed",
                )
                approve_flags[uid] = approve_checked
            else:
                cols[6].write("✔")

        submitted = st.form_submit_button("Lưu cập nhật tất cả")

        if submitted:
            for u in users:
                uid = u["id"]
                old_btc = u["is_btc"]
                old_admin = u["is_admin"]
                old_approved = u["is_approved"]

                ni_btc = new_is_btc.get(uid, old_btc)
                ni_admin = new_is_admin.get(uid, old_admin)

                # Nếu tick duyệt thì cho approved = 1, không hỗ trợ bỏ duyệt
                new_approved = old_approved
                if uid in approve_flags and approve_flags[uid]:
                    new_approved = 1

                # Đồng bộ cột role theo 2 flag (cho tương thích cũ)
                if ni_admin:
                    new_role = "admin"
                elif ni_btc:
                    new_role = "btc"
                else:
                    new_role = "player"

                if (ni_btc != old_btc) or (ni_admin != old_admin) or (new_approved != old_approved) or (new_role != u["role"]):
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
            st.success("Đã cập nhật danh sách thành viên.")
            st.rerun()

    conn.close()

def ui_hnpr_page():
    st.subheader("Bảng xếp hạng trình độ HNPR")

    ranking = compute_hnpr()
    if not ranking:
        st.info("Chưa có dữ liệu bảng xếp hạng cá nhân nào.")
        return

    st.write("Bảng HNPR (tính theo trung bình vị trí xếp hạng cá nhân):")
    st.table([
        {
            "Hạng": r["rank"],
            "VĐV": r["full_name"],
            "Vị trí TB": round(r["avg_pos"], 2),
            "Số phiếu": r["vote_count"]
        }
        for r in ranking
    ])

def ui_home():
    st.subheader("HNX Pickleball Allstars")

    st.markdown("### Giải đấu đang diễn ra")
    t_active = get_tournament_active()
    if t_active:
        st.write(f"**{t_active['name']}** – {t_active['location'] or ''}")
        comps = get_competitors(t_active["id"])
        if comps:
            st.markdown("**Danh sách cặp/đội**")
            st.table([{"ID": c["id"], "Tên": c["name"], "Loại": c["kind"]} for c in comps])

            st.markdown("**Bảng xếp hạng hiện tại**")
            standings = compute_standings(t_active["id"])
            if standings:
                st.table([
                    {
                        "Thứ hạng": i + 1,
                        "Tên": s["name"],
                        "Trận thắng": s["wins"],
                        "Hiệu số point": s["diff"],
                    }
                    for i, s in enumerate(standings)
                ])
            else:
                st.info("Chưa có kết quả trận đấu.")
        else:
            st.info("Giải đấu chưa chia cặp/đội.")
    else:
        st.info("Hiện chưa có giải đấu nào được đánh dấu đang diễn ra.")

    st.markdown("---")
    st.markdown("### Bảng xếp hạng HNPR")
    ui_hnpr_page()

    st.markdown("---")
    st.markdown("### Đăng ký / Đăng nhập")
    st.write("Sử dụng menu bên trái để đăng nhập hoặc đăng ký tài khoản mới.")

def ui_profile_page():
    require_login()
    user = st.session_state["user"]
    st.subheader("Trang cá nhân")

    with st.expander("Thông tin cá nhân", expanded=True):
        full_name = st.text_input("Họ tên", value=user["full_name"])
        age = st.number_input("Tuổi", min_value=5, max_value=100, value=user.get("age") or 30, step=1)
        new_password = st.text_input("Đổi mật khẩu (bỏ trống nếu không đổi)", type="password")
        if st.button("Lưu thông tin cá nhân"):
            conn = get_conn()
            cur = conn.cursor()
            if new_password:
                cur.execute("""
                    UPDATE users
                    SET full_name = ?, age = ?, password_hash = ?
                    WHERE id = ?
                """, (full_name, age, hash_password(new_password), user["id"]))
            else:
                cur.execute("""
                    UPDATE users
                    SET full_name = ?, age = ?
                    WHERE id = ?
                """, (full_name, age, user["id"]))
            conn.commit()
            conn.close()
            # refresh session
            st.session_state["user"] = dict(get_user_by_id(user["id"]))
            st.success("Đã cập nhật thông tin.")

    st.markdown("---")
    st.subheader("Bảng xếp hạng cá nhân")

    owner_id = user["id"]
    existing = get_personal_ranking(owner_id)

    players = [p for p in get_all_players(only_approved=True) if p["id"] != owner_id]

    if not players:
        st.info("Chưa có đủ thành viên để tạo bảng xếp hạng.")
        return

    if not existing:
        st.write("Bạn chưa có bảng xếp hạng cá nhân.")
        if st.button("Tạo bảng xếp hạng dựa trên HNPR / ABC"):
            order_ids = get_hnpr_order_or_alpha()
            order_ids = [uid for uid in order_ids if uid != owner_id]
            save_personal_ranking(owner_id, order_ids)
            st.success("Đã tạo bảng xếp hạng cá nhân.")
            st.rerun()
        return

    # Show and allow reordering
    st.write("Kéo lên / xuống bằng nút để thay đổi thứ tự (1 là mạnh nhất).")

    # build order list in session
    if "personal_order" not in st.session_state:
        st.session_state["personal_order"] = [r["ranked_user_id"] for r in existing]

    order = st.session_state["personal_order"]

    for i, uid in enumerate(order):
        player = next((p for p in players if p["id"] == uid), None)
        if not player:
            continue

        cols = st.columns([0.1, 0.6, 0.15, 0.15])
        cols[0].write(i + 1)
        cols[1].write(player["full_name"])

        up_key = f"up_{uid}_{i}"
        down_key = f"down_{uid}_{i}"

        # Nút lên
        if cols[2].button("⬆", key=up_key) and i > 0:
            order[i - 1], order[i] = order[i], order[i - 1]
            st.session_state["personal_order"] = order
            st.rerun()

        # Nút xuống
        if cols[3].button("⬇", key=down_key) and i < len(order) - 1:
            order[i + 1], order[i] = order[i], order[i + 1]
            st.session_state["personal_order"] = order
            st.rerun()


    if st.button("Lưu bảng xếp hạng"):
        save_personal_ranking(owner_id, order)
        st.success("Đã lưu bảng xếp hạng cá nhân.")
    if st.button("Xoá bảng xếp hạng"):
        delete_personal_ranking(owner_id)
        st.session_state.pop("personal_order", None)
        st.success("Đã xoá.")
        st.rerun()

def ui_tournament_page():
    require_role(["admin", "btc"])

    # mode: "list" hoặc "detail"
    if "tournament_view_mode" not in st.session_state:
        st.session_state["tournament_view_mode"] = "list"
    if "selected_tournament_id" not in st.session_state:
        st.session_state["selected_tournament_id"] = None

    mode = st.session_state["tournament_view_mode"]
    t_id = st.session_state["selected_tournament_id"]

    if mode == "detail" and t_id is not None:
        ui_tournament_detail_page(t_id)
    else:
        ui_tournament_list_page()

def ui_tournament_list_page():
    require_role(["admin", "btc"])
    st.subheader("Quản lý giải đấu – Danh sách giải")

    tournaments = get_tournaments()

    if tournaments:
        st.markdown("### Danh sách giải đấu")

        # Header
        header_cols = st.columns([0.07, 0.3, 0.18, 0.2, 0.09, 0.08, 0.08])
        header_cols[0].write("ID")
        header_cols[1].write("Tên giải")
        header_cols[2].write("Thời gian")
        header_cols[3].write("Địa điểm")
        header_cols[4].write("Đang diễn ra?")
        header_cols[5].write("Xem")
        header_cols[6].write("Sửa / Xóa")

        for t in tournaments:
            tid = t["id"]
            cols = st.columns([0.07, 0.3, 0.18, 0.2, 0.09, 0.08, 0.08])

            cols[0].write(tid)
            cols[1].write(t["name"])
            cols[2].write(f"{t['start_date'] or ''} - {t['end_date'] or ''}")
            cols[3].write(t["location"] or "")
            cols[4].write("✔" if t["is_active"] else "")

            # Nút Xem
            if cols[5].button("Xem", key=f"view_t_{tid}"):
                st.session_state["tournament_view_mode"] = "detail"
                st.session_state["selected_tournament_id"] = tid
                st.rerun()

            # Nút Sửa/Xóa
            c_edit, c_del = cols[6].columns(2)
            if c_edit.button("✏", key=f"edit_t_{tid}"):
                st.session_state["editing_tournament_id"] = tid
                st.rerun()
            if c_del.button("🗑", key=f"del_t_{tid}"):
                delete_tournament(tid)
                st.success(f"Đã xoá giải {t['name']}.")
                st.rerun()
    else:
        st.info("Chưa có giải đấu nào.")

    st.markdown("---")

    # Form thêm mới / sửa giải đấu
    editing_id = st.session_state.get("editing_tournament_id")

    if editing_id:
        st.markdown("### Sửa giải đấu")
        t = get_tournament_by_id(editing_id)
    else:
        st.markdown("### Thêm giải đấu mới")
        t = None

    name = st.text_input("Tên giải đấu", value=t["name"] if t else "")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.text_input("Ngày bắt đầu (text)", value=t["start_date"] if t else "")
    with col2:
        end_date = st.text_input("Ngày kết thúc (text)", value=t["end_date"] if t else "")
    location = st.text_input("Địa điểm", value=t["location"] if t else "")
    num_courts = st.number_input(
        "Số sân thi đấu",
        min_value=1,
        max_value=20,
        value=t["num_courts"] if t and t["num_courts"] else 4,
        step=1
    )
    is_active = st.checkbox(
        "Đánh dấu là giải đang diễn ra",
        value=bool(t["is_active"]) if t else False
    )

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Lưu giải đấu"):
            if not name:
                st.warning("Vui lòng nhập tên giải.")
            else:
                tid = editing_id if t else None
                upsert_tournament(tid, name, start_date, end_date, location, num_courts, is_active)
                st.success("Đã lưu giải đấu.")
                st.session_state["editing_tournament_id"] = None
                st.rerun()
    with col_cancel:
        if editing_id and st.button("Hủy sửa"):
            st.session_state["editing_tournament_id"] = None
            st.rerun()

def ui_tournament_detail_page(t_id: int):
    require_role(["admin", "btc"])

    t = get_tournament_by_id(t_id)
    if not t:
        st.warning("Không tìm thấy giải đấu.")
        # quay về list
        st.session_state["tournament_view_mode"] = "list"
        st.session_state["selected_tournament_id"] = None
        st.rerun()

    # Nút quay lại danh sách
    if st.button("⬅ Quay lại danh sách giải đấu"):
        st.session_state["tournament_view_mode"] = "list"
        st.session_state["selected_tournament_id"] = None
        st.rerun()

    st.subheader(f"Quản lý chi tiết giải: {t['name']}")

    # Thông tin chung của giải
    with st.expander("Thông tin chung của giải", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Tên giải:** {t['name']}")
            st.write(f"**Địa điểm:** {t['location'] or ''}")
        with col2:
            st.write(f"**Thời gian:** {t['start_date'] or ''} - {t['end_date'] or ''}")
            st.write(f"**Số sân:** {t['num_courts'] or ''}")
        with col3:
            st.write(f"**Đang diễn ra:** {'✔' if t['is_active'] else ''}")
            st.write(f"**ID:** {t['id']}")

    st.markdown("---")

    # Các tab chức năng như hiện tại, nhưng dùng t_id cố định
    tab_players, tab_groups, tab_pairs, tab_pools, tab_results = st.tabs(
        ["Thành viên tham gia", "Phân nhóm", "Chia cặp/đội", "Phân bảng", "Kết quả & xếp hạng"]
    )

    with tab_players:
        ui_tournament_players(t_id)
    with tab_groups:
        ui_tournament_groups(t_id)
    with tab_pairs:
        ui_tournament_pairs_teams(t_id)
    with tab_pools:
        ui_tournament_pools(t_id)
    with tab_results:
        ui_tournament_results(t_id)

def ui_tournament_players(t_id):
    # 1. Danh sách hiện tại ở trên cùng
    current = get_tournament_players(t_id)
    if current:
        st.table([
            {"VĐV": p["full_name"], "Nhóm": p["group_name"] or ""}
            for p in current
        ])
    else:
        st.info("Chưa có thành viên tham gia giải.")

    st.markdown("---")

    # 2. Ẩn/hiện khu vực thêm/chỉnh sửa danh sách
    flag_key = f"show_add_players_{t_id}"
    if flag_key not in st.session_state:
        st.session_state[flag_key] = False

    btn_col, _ = st.columns([0.3, 0.7])
    if not st.session_state[flag_key]:
        if btn_col.button("➕ Thêm / chỉnh danh sách thành viên", key=f"btn_show_add_{t_id}"):
            st.session_state[flag_key] = True
            st.rerun()
    else:
        if btn_col.button("Ẩn phần thêm thành viên", key=f"btn_hide_add_{t_id}"):
            st.session_state[flag_key] = False
            st.rerun()

    # 3. Khi bật lên thì hiển thị danh sách tick nhiều cột
    if not st.session_state[flag_key]:
        return

    st.markdown("#### Chọn thành viên tham gia giải")

    all_players = get_all_players(only_approved=True)
    current_ids = {p["user_id"] for p in current}

    # Chia thành nhiều cột cho đỡ dài
    num_cols = 3  # có thể đổi thành 4 nếu danh sách rất dài
    cols = st.columns(num_cols)

    # Bắt đầu từ danh sách hiện trong DB, sau đó override theo checkbox
    selected_ids = set(current_ids)

    for i, p in enumerate(all_players):
        col = cols[i % num_cols]
        checked_default = p["id"] in current_ids
        chk = col.checkbox(
            f"{p['full_name']}",
            value=checked_default,
            key=f"tp_{t_id}_{p['id']}",
        )
        if chk:
            selected_ids.add(p["id"])
        else:
            selected_ids.discard(p["id"])

    if st.button("💾 Lưu danh sách tham gia", key=f"save_tp_{t_id}"):
        set_tournament_players(t_id, list(selected_ids))
        st.success("Đã lưu danh sách thành viên tham gia.")
        st.rerun()

def ui_tournament_groups(t_id):
    st.markdown("### Phân nhóm trình độ")

    players = get_tournament_players(t_id)
    if not players:
        st.info("Chưa có thành viên tham gia giải.")
        return

    use_groups = st.checkbox("Có phân nhóm theo trình độ?", value=True)

    if not use_groups:
        if st.button("Bỏ phân nhóm (xoá group_name)"):
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("UPDATE tournament_players SET group_name = NULL WHERE tournament_id = ?", (t_id,))
            conn.commit()
            conn.close()
            st.success("Đã bỏ phân nhóm.")
        return

    num_groups = st.number_input("Số nhóm", min_value=2, max_value=8, value=4, step=1)
    group_defs = []
    total_players = len(players)
    default_size = total_players // num_groups

    for i in range(int(num_groups)):
        cols = st.columns(2)
        name = cols[0].text_input(f"Tên nhóm #{i+1}", value=chr(ord('A') + i), key=f"gname_{t_id}_{i}")
        size = cols[1].number_input(f"Số VĐV nhóm {name}", min_value=1, max_value=total_players, value=default_size, step=1, key=f"gsize_{t_id}_{i}")
        group_defs.append((name, int(size)))

    if group_defs and group_defs[0][1] != group_defs[-1][1]:
        st.warning("Lưu ý: số lượng nhóm mạnh nhất và yếu nhất đang không bằng nhau.")

    if st.button("Tự động phân nhóm theo HNPR", key=f"auto_group_{t_id}"):
        # sort players by HNPR (or alpha)
        hnpr = compute_hnpr()
        score_map = {r["user_id"]: r["avg_pos"] for r in hnpr}
        # smaller avg_pos = stronger
        players_sorted = sorted(players, key=lambda p: (score_map.get(p["user_id"], 9999)))
        # assign
        assigned = {}
        idx = 0
        for name, size in group_defs:
            for _ in range(size):
                if idx >= len(players_sorted):
                    break
                assigned[players_sorted[idx]["user_id"]] = name
                idx += 1

        conn = get_conn()
        cur = conn.cursor()
        for uid, gname in assigned.items():
            cur.execute("""
                UPDATE tournament_players
                SET group_name = ?
                WHERE tournament_id = ? AND user_id = ?
            """, (gname, t_id, uid))
        conn.commit()
        conn.close()
        st.success("Đã phân nhóm theo HNPR.")

    st.markdown("#### Danh sách phân nhóm hiện tại (có thể chỉnh sửa)")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT tp.user_id, tp.group_name, u.full_name
        FROM tournament_players tp
        JOIN users u ON u.id = tp.user_id
        WHERE tp.tournament_id = ?
        ORDER BY u.full_name
    """, (t_id,))
    rows = cur.fetchall()
    conn.close()

    new_groups = {}
    for r in rows:
        cols = st.columns(3)
        cols[0].write(r["full_name"])
        current_g = r["group_name"] or ""
        choice = cols[1].selectbox("Nhóm", options=[""] + [gd[0] for gd in group_defs],
                                   index=([""] + [gd[0] for gd in group_defs]).index(current_g) if current_g in [gd[0] for gd in group_defs] else 0,
                                   key=f"edit_grp_{t_id}_{r['user_id']}")
        new_groups[r["user_id"]] = choice or None

    if st.button("Lưu cập nhật nhóm", key=f"save_grp_{t_id}"):
        conn = get_conn()
        cur = conn.cursor()
        for uid, gname in new_groups.items():
            cur.execute("""
                UPDATE tournament_players
                SET group_name = ?
                WHERE tournament_id = ? AND user_id = ?
            """, (gname, t_id, uid))
        conn.commit()
        conn.close()
        st.success("Đã lưu phân nhóm.")

def ui_tournament_pairs_teams(t_id):
    st.markdown("### Chia cặp / Chia đội")

    players = get_tournament_players(t_id)
    if not players:
        st.info("Chưa có thành viên tham gia giải.")
        return

    mode = st.radio("Kiểu ghép", options=["Ghép theo cặp", "Chia theo đội"])

    if mode == "Ghép theo cặp":
        if st.button("Tự động ghép cặp", key=f"mk_pairs_{t_id}"):
            make_pairs_for_tournament(t_id)
            st.success("Đã ghép cặp.")
    else:
        num_teams = st.number_input("Số đội", min_value=2, max_value=16, value=4, step=1)
        if st.button("Tự động chia đội", key=f"mk_teams_{t_id}"):
            make_teams_for_tournament(t_id, int(num_teams))
            st.success("Đã chia đội.")

    st.markdown("#### Danh sách cặp/đội")
    comps = get_competitors(t_id)
    members_map = get_competitor_members_map(t_id)
    if comps:
        st.table([
            {
                "ID": c["id"],
                "Tên": c["name"],
                "Loại": c["kind"],
                "Thành viên": ", ".join(name for _, name in members_map.get(c["id"], []))
            }
            for c in comps
        ])
    else:
        st.info("Chưa có cặp/đội nào.")

def make_pairs_for_tournament(t_id):
    players = get_tournament_players(t_id)
    if len(players) < 2:
        st.warning("Cần ít nhất 2 VĐV.")
        return

    # sort by group (A strongest), then HNPR
    hnpr = compute_hnpr()
    score_map = {r["user_id"]: r["avg_pos"] for r in hnpr}
    def group_index(gname):
        if not gname:
            return 99
        return ord(gname[0].upper()) - ord('A')

    players_sorted = sorted(players, key=lambda p: (group_index(p["group_name"]), score_map.get(p["user_id"], 9999)))

    if len(players_sorted) % 2 != 0:
        st.warning("Số VĐV lẻ, 1 người sẽ không được ghép cặp.")
    # pair strongest với yếu nhất dần vào
    pairs = []
    left = 0
    right = len(players_sorted) - 1
    while left < right:
        pairs.append((players_sorted[left]["user_id"], players_sorted[right]["user_id"]))
        left += 1
        right -= 1

    clear_competitors_and_matches(t_id)
    conn = get_conn()
    for i, (u1, u2) in enumerate(pairs, start=1):
        name = f"Cặp {i}"
        create_competitor(conn, t_id, name, "pair", [u1, u2])
    conn.commit()
    conn.close()

def make_teams_for_tournament(t_id, num_teams):
    players = get_tournament_players(t_id)
    if len(players) < num_teams:
        st.warning("Số đội nhiều hơn số VĐV.")
        return

    # sort by group / HNPR như trên
    hnpr = compute_hnpr()
    score_map = {r["user_id"]: r["avg_pos"] for r in hnpr}
    def group_index(gname):
        if not gname:
            return 99
        return ord(gname[0].upper()) - ord('A')
    players_sorted = sorted(players, key=lambda p: (group_index(p["group_name"]), score_map.get(p["user_id"], 9999)))

    # chia vòng tròn lần lượt vào các đội để cân bằng
    teams_members = {i: [] for i in range(num_teams)}
    team_idx = 0
    for p in players_sorted:
        teams_members[team_idx].append(p["user_id"])
        team_idx = (team_idx + 1) % num_teams

    clear_competitors_and_matches(t_id)
    conn = get_conn()
    for i in range(num_teams):
        name = f"Đội {i+1}"
        create_competitor(conn, t_id, name, "team", teams_members[i])
    conn.commit()
    conn.close()

def ui_tournament_pools(t_id):
    st.markdown("### Phân bảng (giai đoạn vòng tròn)")

    comps = get_competitors(t_id)
    if not comps:
        st.info("Cần có cặp/đội trước khi phân bảng.")
        return

    num_pools = st.number_input("Số bảng", min_value=1, max_value=16, value=4, step=1)
    adv_per_pool = st.number_input("Số cặp/đội đi tiếp mỗi bảng", min_value=1, max_value=16, value=2, step=1)

    if st.button("Tự động phân bảng", key=f"mk_pools_{t_id}"):
        # gán pool_name trực tiếp cho competitors theo round-robin
        pool_names = [chr(ord('A') + i) for i in range(int(num_pools))]
        conn = get_conn()
        cur = conn.cursor()
        idx = 0
        for c in comps:
            pool = pool_names[idx % len(pool_names)]
            cur.execute("""
                UPDATE competitors
                SET pool_name = ?
                WHERE id = ?
            """, (pool, c["id"]))
            idx += 1
        conn.commit()
        conn.close()
        st.success("Đã phân bảng.")

    st.info("Thông tin số đội đi tiếp mỗi bảng hiện chỉ lưu trên màn hình (adv_per_pool), bạn có thể ghi chú lại trong biên bản giải.")

    comps = get_competitors(t_id)
    if comps:
        st.markdown("#### Kết quả phân bảng")
        st.table([
            {"ID": c["id"], "Tên": c["name"], "Bảng": c["pool_name"] or ""}
            for c in comps
        ])

def ui_tournament_results(t_id):
    st.markdown("### Ghi nhận kết quả & xếp hạng")

    comps = get_competitors(t_id)
    if not comps:
        st.info("Chưa có cặp/đội.")
        return

    comp_map = {f"{c['id']} - {c['name']}": c["id"] for c in comps}
    col1, col2 = st.columns(2)
    with col1:
        sel1 = st.selectbox("Cặp/Đội 1", list(comp_map.keys()), key=f"m_c1_{t_id}")
        score1 = st.number_input("Point đội 1", min_value=0, max_value=100, value=11, step=1, key=f"m_s1_{t_id}")
    with col2:
        sel2 = st.selectbox("Cặp/Đội 2", list(comp_map.keys()), key=f"m_c2_{t_id}")
        score2 = st.number_input("Point đội 2", min_value=0, max_value=100, value=9, step=1, key=f"m_s2_{t_id}")

    if st.button("Ghi nhận kết quả (BTC xác nhận luôn)", key=f"m_add_{t_id}"):
        c1 = comp_map[sel1]
        c2 = comp_map[sel2]
        if c1 == c2:
            st.warning("Hai đội phải khác nhau.")
        else:
            reporter_id = st.session_state["user"]["id"] if "user" in st.session_state and st.session_state["user"] else None
            add_match(t_id, c1, c2, int(score1), int(score2), reporter_id, auto_confirm=True)
            st.success("Đã ghi nhận kết quả.")
            st.rerun()

    st.markdown("#### Danh sách trận đấu")
    matches = get_matches(t_id)
    if matches:
        st.table([
            {
                "ID": m["id"],
                "Đội 1": m["name1"],
                "Đội 2": m["name2"],
                "Tỉ số": f"{m['score1']} - {m['score2']}",
            }
            for m in matches
        ])
    else:
        st.info("Chưa có trận đấu nào.")

    st.markdown("#### Bảng xếp hạng hiện tại")
    standings = compute_standings(t_id)
    if standings:
        st.table([
            {
                "Hạng": i + 1,
                "Tên": s["name"],
                "Trận thắng": s["wins"],
                "Điểm ghi được": s["pts_for"],
                "Điểm bị thua": s["pts_against"],
                "Hiệu số": s["diff"],
            }
            for i, s in enumerate(standings)
        ])
    else:
        st.info("Chưa đủ dữ liệu để xếp hạng.")

# ------------------ Main app ------------------ #

def main():
    st.set_page_config(page_title="HNX Pickleball Allstars", layout="wide")
    init_db()

    if "user" not in st.session_state:
        st.session_state["user"] = None

    st.sidebar.title("HNX Pickleball Allstars")

    # Hiển thị thông tin login / logout
    if st.session_state["user"]:
        u = st.session_state["user"]
        tags = []
        if u.get("is_admin"):
            tags.append("Admin")
        if u.get("is_btc"):
            tags.append("BTC")
        if not tags:
            tags.append("Player")
        role_str = ", ".join(tags)
        st.sidebar.write(f"Xin chào, **{u['full_name']}** ({role_str})")
        if st.sidebar.button("Đăng xuất"):
            st.session_state["user"] = None
            st.rerun()
    else:
        st.sidebar.write("Chưa đăng nhập.")

        st.sidebar.write("Chưa đăng nhập.")

    # Xây menu theo trạng thái đăng nhập + vai trò
    if st.session_state["user"] is None:
        # Chưa đăng nhập
        menu = ["Trang chủ", "Đăng nhập/Đăng ký", "Bảng HNPR"]
    else:
        u = st.session_state["user"]
        is_admin = bool(u.get("is_admin", 0))
        is_btc = bool(u.get("is_btc", 0))

        # Đã đăng nhập
        menu = ["Trang chủ", "Bảng HNPR", "Trang cá nhân"]

        # Admin hoặc BTC được thêm các menu quản lý
        if is_admin or is_btc:
            menu.insert(2, "Quản lý thành viên")
            menu.insert(3, "Quản lý giải đấu")


        # LƯU Ý: không cho hiện "Đăng nhập/Đăng ký" nữa khi đã logged in

    choice = st.sidebar.radio("Menu", menu, index=0)

    # Điều hướng theo menu
    if choice == "Trang chủ":
        ui_home()
    elif choice == "Đăng nhập/Đăng ký":
        ui_login_register()
    elif choice == "Quản lý thành viên":
        ui_member_management()
    elif choice == "Bảng HNPR":
        ui_hnpr_page()
    elif choice == "Quản lý giải đấu":
        ui_tournament_page()

    elif choice == "Trang cá nhân":
        ui_profile_page()

if __name__ == "__main__":
    main()