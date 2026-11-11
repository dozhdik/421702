import pytest

from omis_blog import domain as d
from omis_blog.controllers import (
    FeedController, ModerationController, ReportController,
    PublicationController, NotificationController,
)
from omis_blog.patterns import (
    RejectArticleCommand, PublishArticleCommand, HideCommentCommand,
    DeleteCommentCommand, AutoFilterStrategy, ManualModerationStrategy,
)
from omis_blog.storage import (
    Database, ComplaintRepository, CommentRepository,
    ReportRepository, ArticleRepository,
)


@pytest.fixture
def system():
    db = Database()
    articles = ArticleRepository(db)
    comments = CommentRepository(db)
    complaints = ComplaintRepository(db)
    notices = NotificationController(db)
    yield db, articles, comments, complaints, PublicationController(articles, notices), ModerationController(comments, complaints, notifications=notices)
    db.close()


def test_publication_rejection_resubmission_and_index(system):
    db, articles, _, _, publications, _ = system
    db.save(d.User(user_id="user"))
    db.save(d.User(user_id="editor-user"))
    db.save(d.Editor(editor_id="editor", user_id="editor-user"))
    author = d.ContentAuthor(user_id="user")
    rubric = d.Category(name="Новости")
    db.save(author)
    db.save(rubric)
    article = d.Article(title="Событие", content="Новости компании", author_id=author.author_id, category_id=rubric.category_id)
    articles.save(article)
    publications.process_submission(article)
    publications.return_for_revision(article.article_id, "editor", "Исправьте")
    assert articles.get_by_id(article.article_id).publication_status == d.ArticleStatus.NEEDS_REVISION
    article = articles.get_by_id(article.article_id)
    article.content = "Исправлено"
    publications.process_submission(article)
    publications.publish_material(article.article_id, "editor")
    assert FeedController(articles).search("Событие") == [articles.get_by_id(article.article_id)]
    assert len(db.list_entities(d.PublicationRecord)) == 1
    assert len(db.list_entities(d.EditorRemark)) == 1


def test_submission_rejects_incomplete_draft_without_ticket(system):
    db, articles, _, _, publications, _ = system
    draft = d.Article(title="Неполная")
    articles.save(draft)
    with pytest.raises(d.DomainException):
        publications.process_submission(draft)
    assert articles.get_by_id(draft.article_id).publication_status == d.ArticleStatus.DRAFT
    assert db.list_entities(d.ModerationQueueEntry) == []


def test_complaint_threshold_unique_and_both_decisions(system):
    db, articles, comments, complaints, _, moderation = system
    article = d.Article()
    db.save(article)
    for reader_id in ("owner", "0", "1", "2"):
        db.save(d.User(user_id=reader_id))
        db.save(d.Reader(reader_id=reader_id, user_id=reader_id))
    for decision in ("confirm", "dismiss"):
        comment = d.Comment(article_id=article.article_id, reader_id="owner", text="Текст")
        comments.save(comment)
        for i in range(3):
            moderation.register_complaint(d.Complaint(comment_id=comment.comment_id, reader_id=str(i)))
            assert comments.get_by_id(comment.comment_id).status == (
                d.CommentStatus.HIDDEN if i == 2 else d.CommentStatus.VISIBLE)
            assert bool(complaints.get_complaint_queue()) == (i == 2)
        with pytest.raises(d.DomainException):
            moderation.register_complaint(d.Complaint(comment_id=comment.comment_id, reader_id="0"))
        assert complaints.get_complaint_count(comment.comment_id) == 3
        moderation.apply_decision(decision, comment.comment_id)
        expected = d.CommentStatus.DELETED if decision == "confirm" else d.CommentStatus.VISIBLE
        assert comments.get_by_id(comment.comment_id).status == expected
        assert len(moderation.notifications.inbox("0")) >= 1
        if decision == "confirm":
            assert len(moderation.notifications.inbox("owner")) == 1


def test_four_commands_restore_prior_state(system):
    db, articles, comments, _, _, _ = system
    for cls in (PublishArticleCommand, RejectArticleCommand):
        article = d.Article(publication_status=d.ArticleStatus.IN_MODERATION)
        articles.save(article)
        command = cls(articles, article.article_id)
        command.execute()
        assert articles.get_by_id(article.article_id).publication_status != d.ArticleStatus.IN_MODERATION
        command.undo()
        assert articles.get_by_id(article.article_id).publication_status == d.ArticleStatus.IN_MODERATION
    for cls in (HideCommentCommand, DeleteCommentCommand):
        comment = d.Comment()
        comments.save(comment)
        command = cls(comments, comment.comment_id)
        command.execute()
        command.undo()
        assert comments.get_by_id(comment.comment_id).status == d.CommentStatus.VISIBLE


def test_strategy_and_report(system):
    db, _, comments, complaints, _, _ = system
    assert ManualModerationStrategy().check("текст")
    auto = AutoFilterStrategy({"спам"})
    alternative = ModerationController(comments, complaints, strategy=auto)
    assert alternative.strategy is auto
    assert not alternative.strategy.check("спам")
    assert alternative.strategy.check("чисто")
    report = ReportController(ReportRepository(db)).generate_report("2000-01-01/2100-01-01")
    assert report.publication_count == 0
    assert report.reach_metric == 0


def test_report_counts_persisted_activity(system):
    db, articles, comments, _, _, _ = system
    article = d.Article(publication_status=d.ArticleStatus.PUBLISHED,
                       published_at=d.utc_now())
    articles.save(article)
    comments.save(d.Comment(article_id=article.article_id))
    db.save(d.Reader(reader_id="reader"))
    db.save(d.Reaction(article_id=article.article_id, reader_id="reader"))
    db.connection.execute('INSERT INTO article_view VALUES (?, ?, ?)',
                          (d.new_id(), article.article_id, d.utc_now().isoformat()))
    db.connection.commit()
    report = ReportController(ReportRepository(db)).generate_report("2000-01-01/2100-01-01")
    assert (report.publication_count, report.comment_count, report.reaction_count, report.reach_metric) == (1, 1, 1, 1.0)


def test_feed_filters_and_pagination_exclude_drafts(system):
    db, articles, _, _, publications, _ = system
    author = d.ContentAuthor(full_name="Иван Автор")
    rubric = d.Category(name="Технологии")
    db.save(author)
    db.save(rubric)
    tag = d.Tag(keyword="платформа")
    for index in range(12):
        article = d.Article(title=f"Событие {index}", content="Текст", author_id=author.author_id,
                           category_id=rubric.category_id)
        articles.save(article)
        db.set_article_tags(article.article_id, [tag])
        publications.process_submission(article)
        publications.publish_material(article.article_id)
    draft = d.Article(title="Черновик", author_id=author.author_id)
    articles.save(draft)
    feed = FeedController(articles)
    first = feed.search(page=1)
    second = feed.search(page=2)
    assert len(first) == 10 and len(second) == 2
    assert not set(a.article_id for a in first) & set(a.article_id for a in second)
    assert all(a.article_id != draft.article_id for a in first + second)
    assert len(feed.search("Событие")) == 10
    assert len(feed.search(author="Иван")) == 10
    assert len(feed.search(category=rubric.category_id)) == 10
    assert len(feed.search(tag="платформа")) == 10
