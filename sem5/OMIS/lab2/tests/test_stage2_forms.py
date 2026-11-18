from omis_blog import domain as d
from omis_blog.auth import hash_password
from omis_blog.main import BlogPlatformApp
from omis_blog.web import WebApp, render_markdown
from tests.test_web import Client


def test_form_errors_keep_safe_values(tmp_path):
    app = BlogPlatformApp(tmp_path / 'forms.sqlite')
    app.initialize_system()
    role = d.Role(role_name='Author')
    user = d.User(full_name='Existing User')
    account = d.UserAccount(login='existing', password_hash=hash_password('password123'),
                            user_id=user.user_id, role_id=role.role_id)
    for obj in (role, user, account, d.AccessPermission(role_id=role.role_id, operation_code='article.write'),
                d.ContentAuthor(full_name=user.full_name, user_id=user.user_id)):
        app.db.save(obj)
    client = Client(WebApp(app))
    client.request('/register')
    status, body, _ = client.request('/register', {'full_name': 'Test <Name>', 'login': 'existing',
                                                   'password': 'password123', 'confirmation': 'password123'})
    assert status == '400 Bad Request'
    assert 'Этот логин уже занят' in body and 'Test &lt;Name&gt;' in body
    assert 'value="password123"' not in body and 'role="alert"' in body
    client.request('/login')
    assert client.request('/login', {'login': 'existing', 'password': 'password123'})[0] == '303 See Other'
    client.request('/editor/new')
    status, body, _ = client.request('/article/save', {'title': '', 'content': 'Important <text>',
        'tags': 'one, two', 'rubric': '', 'action': 'submit'})
    assert status == '400 Bad Request'
    assert 'Important &lt;text&gt;' in body and 'one, two' in body
    assert 'Нужны заголовок' in body
    app.db.close()


def test_editor_formatting_renders_without_enabling_raw_html():
    text = '## **План**\n\n*Пример*: **<img src=x onerror=alert(1)>**'
    assert render_markdown(text) == ('<h2><strong>План</strong></h2>'
                                     '<p><em>Пример</em>: <strong>&lt;img src=x onerror=alert(1)&gt;</strong></p>')
