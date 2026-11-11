"""E.5 application entry point."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
from wsgiref.simple_server import WSGIServer, make_server

from omis_blog import domain as d
from omis_blog.infrastructure import SystemConfigurator, DependencyContainer
from omis_blog.storage import Database


class BlogPlatformApp:
    def __init__(self, database_path: str | Path = "blog.sqlite", host: str = "127.0.0.1", port: int = 8000) -> None:
        self.db = Database(database_path)
        self.container = DependencyContainer()
        self.configurator = SystemConfigurator(self.db)
        self.controllers: list[Any] = []
        self.views: list[Any] = []
        self.host = host
        self.port = port
        self.server: WSGIServer | None = None

    @staticmethod
    def main(args: list[str] | None = None) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("--db", default="blog.sqlite")
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=8000)
        parsed = parser.parse_args(args)
        if parsed.db != ":memory:":
            probe = Database(parsed.db)
            is_fresh = not probe.list_entities(d.UserAccount)
            probe.close()
            if is_fresh:
                from scripts.seed_demo import seed
                seed(parsed.db)
        app = BlogPlatformApp(parsed.db, parsed.host, parsed.port)
        app.initialize_system()
        try:
            app.start_application()
        except KeyboardInterrupt:
            print("Application stopped")
        finally:
            app.stop_application()

    def initialize_system(self) -> None:
        self.configurator.configure_dependencies(self.container)
        repos = self.configurator.create_repositories()
        self.controllers = self.configurator.create_controllers(repos)
        self.views = self.configurator.create_views(self.controllers)
        self.configurator.connect_components()

    def start_application(self) -> None:
        from omis_blog.web import WebApp

        self.server = make_server(self.host, self.port, WebApp(self))
        self.server.serve_forever()

    def stop_application(self) -> None:
        if self.server:
            self.server.server_close()
            self.server = None
        self.db.close()


if __name__ == "__main__":
    BlogPlatformApp.main()
