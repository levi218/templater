def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('upload', '/upload')
    config.add_route('files', '/files')
    config.add_route('verify', '/verify')
    config.add_route('render', '/render')
