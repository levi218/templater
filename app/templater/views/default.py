from pyramid.view import view_config
from pyramid.response import FileIter
from bson import ObjectId
from templater.lib.templater import RenderResult, TemplateRenderer
from tempfile import NamedTemporaryFile
import time 
import urllib
import datetime
@view_config(route_name='home', renderer='../templates/homepage.jinja2')
def home_page(request):
    return {'project': 'Templater'}
    

@view_config(route_name='upload', request_method='POST', renderer='json')
def upload_doc(request):
    file_id = request.fs.put(request.POST['file'].file, filename = request.POST['file'].filename)
    max_age = request.registry.settings['templater']['file_max_age'] if request.registry.settings['templater']['file_max_age'] else 60
    delta = datetime.timedelta(minutes=int(max_age))
    if 'table-preview' in request.POST:
        datafile = request.fs.get(ObjectId(file_id))
        renderer = TemplateRenderer()
        renderer.load_data(datafile)
        return {'status': 'OK', 'file_id':str(file_id), 'data': renderer.raw_table, 'expire_at': (datetime.datetime.utcnow() + delta).isoformat()}    
    return {'status': 'OK', 'file_id':str(file_id), 'expire_at': (datetime.datetime.utcnow() + delta).isoformat()}

@view_config(route_name='files', request_method='GET')
def get_doc(request):
    file_id = ObjectId(request.GET['file_id'])
    file = request.fs.get(file_id)

    response = request.response
    response.app_iter = FileIter(file)
    response.content_disposition = "attachment; filename*=UTF-8''%s" % urllib.parse.quote(file.name.encode('utf8'))

    return response

@view_config(route_name='verify', request_method='POST', renderer='json')
def verify_doc(request):
    # try:
        template_id = request.POST['template-id']
        data_id = request.POST['data-table-id']
        
        template = request.fs.get(ObjectId(template_id))
        data = request.fs.get(ObjectId(data_id))

        renderer = TemplateRenderer()

        renderer.load_data(data)
        result = renderer.verify(template)

        return {'status': 'OK', 'messages': result, 'fields': renderer.fieldnames}
    # except:
    #     return {'status': 'err'}

@view_config(route_name='render', request_method='POST', renderer='json')
def render_doc(request):
    # try:
        template_id = request.POST['template-id']
        data_id = request.POST['data-table-id']
        name_pattern = request.POST['name-pattern'] if 'name-pattern' in request.POST else None
        
        template = request.fs.get(ObjectId(template_id))
        data = request.fs.get(ObjectId(data_id))

        renderer = TemplateRenderer()

        renderer.load_data(data)
        result = renderer.render(template, name_pattern)

        files_id = {}
        for filename in result.files:
            # tmp = NamedTemporaryFile()
            try:
                tmp = request.fs.new_file(filename = filename)
                tmp.write(result.files[filename].getvalue())
            finally:
                tmp.close()
                files_id[filename] = str(tmp._id)
        
        archive_id = None
        if(result.archive is not None):
            try:
                tmp = request.fs.new_file(filename = "archive.zip")
                tmp.write(result.archive.getvalue())
            finally:
                tmp.close()
                archive_id = str(tmp._id)

        return {'status': 'OK', 'files': files_id, 'archive': str(archive_id) if archive_id is not None else ''}
    # except:
    #     return {'status': 'err'}