import re

def test_leaderboard_rows_are_closed(make_game, player):
    _, game = make_game("Game")
    clients = [player(name) for name in ("alice", "bob", "carol")]
    for c in clients:
        c.post(f"/games/{game}/login")

    for c in (clients[0], clients[1]):  # owner and non-owner
        tbody = re.search(r"<tbody>(.*?)</tbody>", c.get(f"/games/{game}").data.decode(), re.DOTALL).group(1)
        assert len(re.findall(r"<tr\b", tbody)) == 3
        assert tbody.count("</tr>") == 3
