class DevStaticCacheMiddleware:
    """
    Middleware that disables caching for static and media files during development.
    Ensures browsers immediately receive and apply updated CSS/JS across all page navigations
    without requiring manual hard-refreshes.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
