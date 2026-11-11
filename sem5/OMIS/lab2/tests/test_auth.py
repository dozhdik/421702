from omis_blog import domain as d
from omis_blog.auth import authenticate, has_permission, hash_password
from omis_blog.storage import Database


def test_password_active_status_and_server_rights(tmp_path):
    db = Database(tmp_path / "auth.sqlite")
    role = d.Role(role_name="Автор")
    user = d.User(full_name="Автор")
    account = d.UserAccount(login="alice", password_hash=hash_password("secret"),
                              user_id=user.user_id, role_id=role.role_id)
    user.account_id = account.account_id
    user.password_hash = account.password_hash
    db.save(role)
    db.save(user)
    db.save(account)
    db.save(d.AccessPermission(operation_code="article.write", role_id=role.role_id))
    assert authenticate(db, "alice", "secret") == account
    assert authenticate(db, "alice", "wrong") is None
    assert has_permission(db, account, "article.write")
    assert not has_permission(db, account, "article.moderate")
    assert db.get(d.User, user.user_id).password_hash == account.password_hash
    account.is_active = False
    db.save(account)
    assert authenticate(db, "alice", "secret") is None
    assert not has_permission(db, account, "article.write")
