import pytest

from omis_blog.domain import InvalidTransition, ARTICLE_TRANSITIONS, ArticleStatus, Article


def test_all_transitions_are_enforced():
    for old in ArticleStatus:
        for new in ArticleStatus:
            article = Article(publication_status=old)
            if new in ARTICLE_TRANSITIONS[old]:
                article.transition_to(new)
                assert article.publication_status == new
            else:
                with pytest.raises(InvalidTransition):
                    article.transition_to(new)


def test_incomplete_draft_is_allowed_but_not_submittable():
    article = Article()
    assert article.publication_status == ArticleStatus.DRAFT
    assert not article.ready_for_moderation()
    article.title, article.content, article.category_id = "Заголовок", "Текст", "rubric"
    assert article.ready_for_moderation()
