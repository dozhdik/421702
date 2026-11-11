from omis_blog.controllers import FeedController
from omis_blog.main import BlogPlatformApp
from omis_blog.presentation import IFeedView
from omis_blog.storage import IRepository, ArticleRepository


def test_configurator_creates_and_links_all_components():
    app = BlogPlatformApp(":memory:")
    app.initialize_system()
    assert len(app.controllers) == 5
    assert len(app.views) == 4
    assert app.container.resolve(FeedController) is app.controllers[3]
    assert isinstance(app.container.resolve(IRepository), ArticleRepository)
    assert app.container.create_view(IFeedView) is app.views[0]
    assert app.controllers[3].view is app.views[0]
    app.stop_application()
