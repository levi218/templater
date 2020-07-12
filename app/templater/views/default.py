from pyramid.view import view_config
from pyramid.response import FileIter
from bson import ObjectId
from templater.lib.templater import RenderResult, TemplateRenderer
from tempfile import NamedTemporaryFile
import time 
import datetime
@view_config(route_name='home', renderer='../templates/mytemplate.jinja2')
def my_view(request):
    # mydict = { "name": "Peter", "address": "Lowstreet 27" }
    print(request.db.list_collection_names())
    # x = request.db['test'].insert_one(mydict)

    # print(x.inserted_id)
    return {'project': 'Templater'}
    

@view_config(route_name='upload', request_method='POST', renderer='json')
def upload_doc(request):
    print(request.POST['file'].file)
    file_id = request.fs.put(request.POST['file'].file, filename = request.POST['file'].filename)
    return {'status': 'OK', 'file_id':str(file_id)}

@view_config(route_name='files', request_method='GET')
def get_doc(request):
    file_id = ObjectId(request.GET['file_id'])
    file = request.fs.get(file_id)

    response = request.response
    response.app_iter = FileIter(file)
    response.content_disposition = 'attachment; filename="%s"' % file.name

    return response

@view_config(route_name='verify', request_method='POST', renderer='json')
def verify_doc(request):
    template_id = request.POST['template-id']
    data_id = request.POST['data-table-id']
    
    template = request.fs.get(ObjectId(template_id))
    data = request.fs.get(ObjectId(data_id))

    renderer = TemplateRenderer()

    lines = data.read().decode("utf-8-sig").splitlines()
    renderer.load_csv(lines, ',')
    result = renderer.verify(template)

    return {'status': 'OK', 'messages': result, 'fields': renderer.fieldnames}

@view_config(route_name='render', request_method='POST', renderer='json')
def render_doc(request):
    start = time.time()
    template_id = request.POST['template-id']
    data_id = request.POST['data-table-id']
    name_pattern = request.POST['name-pattern'] if 'name-pattern' in request.POST else None
    
    print(time.time()-start)
    template = request.fs.get(ObjectId(template_id))
    data = request.fs.get(ObjectId(data_id))
    print(time.time()-start)

    renderer = TemplateRenderer()

    lines = data.read().decode("utf-8-sig").splitlines()
    renderer.load_csv(lines, ',')
    result = renderer.render(template, name_pattern)

    print(time.time()-start)
    files_id = {}
    for filename in result.files:
        # tmp = NamedTemporaryFile()
        try:
            tmp = request.fs.new_file(filename = filename)
            tmp.write(result.files[filename].getvalue())
        finally:
            tmp.close()
            files_id[filename] = str(tmp._id)
    
    print(time.time()-start)
    archive_id = None
    if(result.archive is not None):
        try:
            tmp = request.fs.new_file(filename = "archive.zip")
            tmp.write(result.archive.getvalue())
        finally:
            tmp.close()
            archive_id = str(tmp._id)
    print(time.time()-start)

    return {'status': 'OK', 'files': files_id, 'archive': str(archive_id) if archive_id is not None else ''}