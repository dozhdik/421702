from dataclasses import fields
from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from omis_blog import domain as d
from omis_blog.storage import Database, ENTITIES
from scripts.seed_demo import seed


def test_every_entity_roundtrips_across_restart(tmp_path):
    path = tmp_path / "blog.sqlite"
    db = Database(path)
    objects = [cls() for cls in ENTITIES]
    for obj in objects:
        if isinstance(obj, d.UserAccount):
            obj.login = "user"
        db.save(obj)
    db.close()
    reopened = Database(path)
    for obj in objects:
        key = fields(obj)[0].name
        restored = reopened.get(type(obj), getattr(obj, key))
        assert restored is not None
        if isinstance(obj, d.User):
            assert restored.full_name == obj.full_name
        else:
            assert restored == obj
    reopened.close()


def test_article_tags_are_persistent(tmp_path):
    db = Database(tmp_path / "tags.sqlite")
    article = d.Article()
    tag = d.Tag(keyword="Новости")
    db.save(article)
    db.set_article_tags(article.article_id, [tag])
    db.close()
    reopened = Database(tmp_path / "tags.sqlite")
    assert reopened.get_article_tags(article.article_id) == [tag]


def test_foreign_keys_reject_broken_relations(tmp_path):
    db = Database(tmp_path / "constraints.sqlite")
    with pytest.raises(sqlite3.IntegrityError):
        db.save(d.Article(author_id="missing"))
    article = d.Article()
    db.save(article)
    with pytest.raises(sqlite3.IntegrityError):
        db.save(d.Comment(article_id=article.article_id, parent_id="missing"))
    with pytest.raises(d.DomainException):
        db.save(d.Article(created_at=datetime(2020, 1, 1)))
    offset_date = datetime(2020, 1, 1, tzinfo=timezone(timedelta(hours=3)))
    converted = d.Article(created_at=offset_date)
    db.save(converted)
    assert db.get(d.Article, converted.article_id).created_at.utcoffset() == timedelta(0)


def test_seed_is_idempotent_and_survives_restart(tmp_path):
    path = tmp_path / "seed.sqlite"
    seed(str(path))
    seed(str(path))
    db = Database(path)
    assert len(db.list_entities(d.UserAccount)) == 4
    assert len(db.list_entities(d.Article)) == 8
    assert len(db.list_entities(d.Complaint)) == 2
    assert len(db.list_entities(d.SearchIndex)) == 6
    db.close()
