
import streamlit as st
import copy
import random

st.set_page_config(page_title="Cờ Tướng Bot", page_icon="♟️", layout="wide")

# K = Tướng, A = Sĩ, E = Tượng, R = Xe,
# H = Mã, C = Pháo, P = Tốt
# Chữ hoa: Đỏ (bot). Chữ thường: Đen (bạn).

SYMBOLS = {
    "K": "帥", "A": "仕", "E": "相", "R": "俥",
    "H": "傌", "C": "炮", "P": "兵",
    "k": "將", "a": "士", "e": "象", "r": "車",
    "h": "馬", "c": "砲", "p": "卒",
}

VALUES = {"K": 10000, "A": 120, "E": 120,
          "R": 600, "H": 300, "C": 300, "P": 70}

DEPTHS = {"Dễ": 1, "Trung bình": 2, "Khó": 3}


def new_board():
    b = [[None for _ in range(9)] for _ in range(10)]
    back = list("rheakaehr")
    # Hàng quân phía trên: Đen (người chơi)
    b[0] = back[:]
    for c in (1, 7):
        b[2][c] = "c"
    for c in (0, 2, 4, 6, 8):
        b[3][c] = "p"

    # Hàng quân phía dưới: Đỏ (bot)
    b[9] = list("RHEAKAEHR")
    for c in (1, 7):
        b[7][c] = "C"
    for c in (0, 2, 4, 6, 8):
        b[6][c] = "P"
    return b


def inside(r, c):
    return 0 <= r < 10 and 0 <= c < 9


def own(p, side):
    if p is None:
        return False
    return p.isupper() if side == "R" else p.islower()


def palace(r, c, side):
    if not 3 <= c <= 5:
        return False
    return 7 <= r <= 9 if side == "R" else 0 <= r <= 2


def pseudo_moves(b, r, c):
    p = b[r][c]
    if p is None:
        return []
    side = "R" if p.isupper() else "B"
    red = side == "R"
    kind = p.upper()
    dr = -1 if red else 1
    out = []

    def add(nr, nc):
        if inside(nr, nc) and not own(b[nr][nc], side):
            out.append((nr, nc))

    if kind == "R":  # Xe
        for vr, vc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + vr, c + vc
            while inside(nr, nc):
                if b[nr][nc] is None:
                    out.append((nr, nc))
                else:
                    if not own(b[nr][nc], side):
                        out.append((nr, nc))
                    break
                nr += vr
                nc += vc

    elif kind == "C":  # Pháo
        for vr, vc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + vr, c + vc
            screen = False
            while inside(nr, nc):
                target = b[nr][nc]
                if not screen:
                    if target is None:
                        out.append((nr, nc))
                    else:
                        screen = True
                else:
                    if target is not None:
                        if not own(target, side):
                            out.append((nr, nc))
                        break
                nr += vr
                nc += vc

    elif kind == "H":  # Mã: kiểm tra chân Mã
        for vr, vc in (
            (-2, -1), (-2, 1), (2, -1), (2, 1),
            (-1, -2), (1, -2), (-1, 2), (1, 2)
        ):
            leg = (r + (vr // 2 if abs(vr) == 2 else 0),
                   c + (vc // 2 if abs(vc) == 2 else 0))
            if b[leg[0]][leg[1]] is None:
                add(r + vr, c + vc)

    elif kind == "E":  # Tượng: không qua sông
        for vr, vc in ((-2, -2), (-2, 2), (2, -2), (2, 2)):
            nr, nc = r + vr, c + vc
            if not inside(nr, nc):
                continue
            if red and nr < 5:
                continue
            if not red and nr > 4:
                continue
            if b[r + vr // 2][c + vc // 2] is None:
                add(nr, nc)

    elif kind == "A":  # Sĩ
        for vr, vc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            nr, nc = r + vr, c + vc
            if palace(nr, nc, side):
                add(nr, nc)

    elif kind == "K":  # Tướng
        for vr, vc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + vr, c + vc
            if palace(nr, nc, side):
                add(nr, nc)

        # Hai Tướng đối mặt trên cùng một cột
        nr = r + dr
        while inside(nr, c):
            if b[nr][c] is not None:
                if b[nr][c] == ("k" if red else "K"):
                    out.append((nr, c))
                break
            nr += dr

    elif kind == "P":  # Tốt
        add(r + dr, c)
        crossed = r <= 4 if red else r >= 5
        if crossed:
            add(r, c - 1)
            add(r, c + 1)

    return out


def move_piece(b, src, dst):
    result = [row[:] for row in b]
    r, c = src
    nr, nc = dst
    result[nr][nc] = result[r][c]
    result[r][c] = None
    return result


def in_check(b, side):
    king = "K" if side == "R" else "k"
    pos = None
    for r in range(10):
        for c in range(9):
            if b[r][c] == king:
                pos = (r, c)
                break
        if pos is not None:
            break
    if pos is None:
        return True

    enemy = "B" if side == "R" else "R"
    for r in range(10):
        for c in range(9):
            if own(b[r][c], enemy):
                if pos in pseudo_moves(b, r, c):
                    return True
    return False


def legal_moves(b, side):
    moves = []
    for r in range(10):
        for c in range(9):
            if own(b[r][c], side):
                for dst in pseudo_moves(b, r, c):
                    test = move_piece(b, (r, c), dst)
                    if not in_check(test, side):
                        moves.append(((r, c), dst))
    return moves


def evaluate(b):
    score = 0
    for r in range(10):
        for c in range(9):
            p = b[r][c]
            if p is None:
                continue
            value = VALUES[p.upper()]
            if p.upper() == "P":
                value += (9 - r) * 5 if p.isupper() else r * 5
            score += value if p.isupper() else -value
    return score


def ordered_moves(b, moves):
    return sorted(
        moves,
        key=lambda m: (
            b[m[1][0]][m[1][1]] is not None,
            random.random()
        ),
        reverse=True
    )


def search(b, depth, side, alpha, beta):
    moves = legal_moves(b, side)
    if not moves:
        return (-100000 if side == "R" else 100000)

    if depth == 0:
        return evaluate(b)

    moves = ordered_moves(b, moves)

    if side == "R":  # Bot đỏ tối đa hóa điểm
        best = -float("inf")
        for src, dst in moves:
            score = search(move_piece(b, src, dst),
                           depth - 1, "B", alpha, beta)
            best = max(best, score)
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    else:  # Người chơi đen tối thiểu hóa điểm của đỏ
        best = float("inf")
        for src, dst in moves:
            score = search(move_piece(b, src, dst),
                           depth - 1, "R", alpha, beta)
            best = min(best, score)
            beta = min(beta, best)
            if alpha >= beta:
                break
        return best


def bot_move(b, depth):
    moves = ordered_moves(b, legal_moves(b, "R"))
    if not moves:
        return b
    best_score = -float("inf")
    best = []
    for src, dst in moves:
        score = search(move_piece(b, src, dst),
                       depth - 1, "B",
                       -float("inf"), float("inf"))
        if score > best_score:
            best_score = score
            best = [(src, dst)]
        elif score == best_score:
            best.append((src, dst))
    src, dst = random.choice(best)
    return move_piece(b, src, dst)


st.title("♟️ CỜ TƯỚNG — ĐẤU VỚI BOT")
st.caption("Bạn cầm quân Đen • Bot cầm quân Đỏ và đi trước")

mode = st.selectbox("Chọn độ khó của bot",
                    ["Dễ", "Trung bình", "Khó"],
                    index=1)
depth = DEPTHS[mode]

if "board" not in st.session_state:
    st.session_state.board = bot_move(new_board(), depth)
    st.session_state.selected = None
    st.session_state.turn = "B"
    st.session_state.over = False
    st.session_state.winner = None

if st.button("🔄 Chơi ván mới"):
    st.session_state.board = bot_move(new_board(), depth)
    st.session_state.selected = None
    st.session_state.turn = "B"
    st.session_state.over = False
    st.session_state.winner = None

b = st.session_state.board

if not st.session_state.over and not legal_moves(b, st.session_state.turn):
    st.session_state.over = True
    st.session_state.winner = "R" if st.session_state.turn == "B" else "B"

if st.session_state.over:
    if st.session_state.winner == "B":
        st.success("🎉 Bạn thắng!")
    else:
        st.error("🤖 Bot thắng! Hãy thử ván khác.")
elif in_check(b, st.session_state.turn):
    st.warning("⚠️ Bạn đang bị chiếu Tướng!")

st.write("### Bàn cờ")
st.caption("Bấm quân Đen của bạn, rồi bấm ô muốn đi.")

selected = st.session_state.selected
destinations = (
    [dst for src, dst in legal_moves(b, "B") if src == selected]
    if selected is not None else []
)

for r in range(10):
    cols = st.columns(9, gap="small")
    for c in range(9):
        p = b[r][c]
        label = SYMBOLS[p] if p else "·"
        if (r, c) == selected:
            label = "🔵 " + label
        elif (r, c) in destinations and p is None:
            label = "◎"
        elif (r, c) in destinations and p is not None:
            label = "⚔️ " + label

        with cols[c]:
            if st.button(
                label,
                key=f"sq_{r}_{c}",
                disabled=st.session_state.over or st.session_state.turn != "B",
                use_container_width=True
            ):
                if p is not None and p.islower():
                    st.session_state.selected = (r, c)
                elif selected is not None and (r, c) in destinations:
                    st.session_state.board = move_piece(
                        b, selected, (r, c)
                    )
                    st.session_state.selected = None

                    if not legal_moves(st.session_state.board, "R"):
                        st.session_state.over = True
                        st.session_state.winner = "B"
                    else:
                        st.session_state.board = bot_move(
                            st.session_state.board, depth
                        )
                        if not legal_moves(st.session_state.board, "B"):
                            st.session_state.over = True
                            st.session_state.winner = "R"
                else:
                    st.session_state.selected = None
                st.rerun()

st.caption(
    "Chế độ hiện tại: " + mode +
    " • Đỏ: Bot • Đen: Bạn"
)
