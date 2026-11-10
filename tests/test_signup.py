import db

def join(client, url_id: str):
    return client.post(f"/games/{url_id}/login")

def test_same_account_joins_two_games(make_game, player):
    _, one = make_game("One")
    _, two = make_game("Two")
    alice = player("alice")

    for url_id in (one, two):
        join(alice, url_id)
        assert b"Welcome, <i>Alice</i>" in alice.get(f"/games/{url_id}").data

def test_first_joiner_owns_each_game(app, make_game, player):
    g1, one = make_game("One")
    g2, two = make_game("Two")
    alice, bob = player("alice"), player("bob")

    join(alice, one)
    join(bob, two)
    join(bob, one)
    join(alice, two)

    with app.app_context():
        assert db.get_game_by_id(g1).owner == "alice"
        assert db.get_game_by_id(g2).owner == "bob"

def test_elimination_only_affects_its_game(app, make_game, player):
    g1, one = make_game("One")
    g2, two = make_game("Two")
    clients = {name: player(name) for name in ("alice", "bob", "carol")}
    for url_id in (one, two):
        for client in clients.values():
            join(client, url_id)
        clients["alice"].post(f"/games/{url_id}/start")

    with app.app_context():
        victim = db.get_user_by_id(g1, "alice").target_user_id
    clients["alice"].post(f"/games/{one}/eliminate_user", data={"user_id": victim, "elim_count": 1})

    with app.app_context():
        assert db.get_user_by_id(g1, victim).eliminated
        assert len(db.get_game_logs(g1)) == 1
        assert not any(u.eliminated for u in db.get_users_by_game(g2))
        assert db.get_game_logs(g2) == []
