"""
Custom middleware for the adlab project.
"""

from django.http import HttpResponseRedirect


class DocsIndexMiddleware:
    """
    Middleware to serve index.html for MkDocs documentation directory URLs.

    MkDocs generates URLs like /static/docs/getting-started/system-overview/
    which should serve /static/docs/getting-started/system-overview/index.html

    This middleware appends 'index.html' to documentation URLs ending with /
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a docs URL ending with /
        if request.path.startswith("/static/docs/") and request.path.endswith("/"):
            # Redirect to the index.html file
            return HttpResponseRedirect(request.path + "index.html")

        response = self.get_response(request)
        return response
