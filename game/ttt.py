#!/usr/bin/env python3
"""Community tic-tac-toe for a GitHub profile README.

A visitor clicks a square -> opens an issue titled "ttt|move|<0-8>".
The workflow runs this script, which updates game/state.json, redraws the
board between the TTT markers in README.md, and writes comment.md for the reply.

  python3 game/ttt.py            # play the move from ISSUE_TITLE / ISSUE_USER
  python3 game/ttt.py --render   # just redraw the board
"""
import json, os, re, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "game" / "state.json"
README = ROOT / "README.md"
COMMENT = ROOT / "comment.md"
REPO = os.environ.get("REPO", "nocaptainangel/nocaptainangel")
LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
EMOJI = {"X": "❌", "O": "⭕"}


def load():
    return json.loads(STATE.read_text())


def save(s):
    STATE.write_text(json.dumps(s, indent=2) + "\n")


def winner(board):
    for a, b, c in LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return "draw" if all(board) else None


def issue_link(i):
    q = urllib.parse.urlencode({
        "title": f"ttt|move|{i}",
        "body": "Just press **Submit new issue** to play your move ✨\n\n(You don't need to write anything.)",
    })
    return f"https://github.com/{REPO}/issues/new?{q}"


def render(s):
    turn = EMOJI[s["turn"]]
    rows = []
    for r in range(3):
        cells = []
        for c in range(3):
            i = r * 3 + c
            v = s["board"][i]
            if v:
                img = f'<img src="assets/{v.lower()}.svg" width="52" alt="{v}">'
            else:
                img = f'<a href="{issue_link(i)}"><img src="assets/empty.svg" width="52" alt="square {i+1}"></a>'
            cells.append(img)
        rows.append(" ".join(cells))
    board = "<br>\n".join(rows)

    moves = s["recent"][:3]
    recent = "<br>\n".join(
        f'{EMOJI[m["piece"]]} <a href="https://github.com/{m["user"]}">@{m["user"]}</a>' for m in moves
    ) or "be the first move ✨"

    last = s.get("last_result")
    last_line = f"<sub>last game: {last}</sub><br>\n" if last else ""

    st = s["stats"]
    block = f"""<!-- TTT:START -->
<p align="center">
<b>let's play tic-tac-toe</b><br>
<sub>it's {turn}'s turn · tap a square</sub><br><br>
{board}<br><br>
<sub><b>recent moves</b></sub><br>
<sub>{recent}</sub><br><br>
{last_line}<sub>🏆 ❌ {st['X']} · ⭕ {st['O']} · 🤝 {st['draw']}</sub>
</p>
<!-- TTT:END -->"""
    text = README.read_text()
    text = re.sub(r"<!-- TTT:START -->.*?<!-- TTT:END -->", block, text, flags=re.S)
    README.write_text(text)


def play():
    title = os.environ.get("ISSUE_TITLE", "")
    user = os.environ.get("ISSUE_USER", "someone")
    s = load()

    m = re.fullmatch(r"ttt\|move\|([0-8])", title.strip())
    if not m:
        return "Hmm, I couldn't read that move. Head back to the profile and tap an empty square 🌱"
    i = int(m.group(1))

    if s["board"][i]:
        return "Ah, someone already took that square. Pick another one on the profile 🌿"
    if s.get("last_player") == user:
        return f"You made the last move, @{user}! Let someone else go first, then come back ✨"

    piece = s["turn"]
    s["board"][i] = piece
    s["last_player"] = user
    s["recent"].insert(0, {"user": user, "piece": piece, "square": i})
    s["recent"] = s["recent"][:10]
    s["turn"] = "O" if piece == "X" else "X"

    w = winner(s["board"])
    if w:
        s["games"] += 1
        if w == "draw":
            s["stats"]["draw"] += 1
            s["last_result"] = "a draw 🤝"
            msg = f"Nice move, @{user}! That's a draw 🤝 A fresh board is waiting."
        else:
            s["stats"][w] += 1
            s["last_result"] = f"{EMOJI[w]} won, finished by @{user}"
            msg = f"🎉 @{user} won it for {EMOJI[w]}! A fresh board is waiting."
        s["board"] = [None] * 9
        s["turn"] = "X"
        s["last_player"] = None
    else:
        msg = f"Nice move, @{user}! You played {EMOJI[piece]} in square {i+1}. Now it's {EMOJI[s['turn']]}'s turn 🌿"

    save(s)
    return msg + "\n\nThe board updates on the profile in a few seconds. Thanks for playing 🤍"


if __name__ == "__main__":
    if "--render" in sys.argv:
        render(load())
    else:
        COMMENT.write_text(play())
        render(load())
