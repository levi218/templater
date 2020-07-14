import csv
import xlrd
from docxtpl import DocxTemplate
from jinja2 import Environment, Template, meta
from .custom_exceptions import TemplateTypeNotSupported, OutputNameTemplateSyntax
from .custom_odt_renderer import CustomOdtRenderer
import re
import io
import zipfile
# defining global variables

class RenderResult(object):
    def __init__(self):
        self.files = {}
        self.archive = None


class TemplateRenderer(object):

    def __init__(self):
        self.contexts = []
        self.fieldnames = []
        self.raw_table = []

    # Load data from csv file
    def load_csv(self, csvfile, delimiter):
        # open csv file and prepare context array
        lines = csvfile.read().decode("utf-8-sig").splitlines()
        reader = csv.DictReader(lines, delimiter=delimiter)
        self.fieldnames = reader.fieldnames
        self.raw_table.append(self.fieldnames)
        for row in reader:
            context = {}
            r = []
            for key, value in row.items():
                context[key] = value
                r.append(value)
            self.contexts.append(context)
            self.raw_table.append(r)

    def load_excel(self, excelfile):
        wb = xlrd.open_workbook(file_contents = excelfile.read()) 
        sh = wb.sheet_by_index(0)
        for col in range(sh.ncols):
            self.fieldnames.append(sh.cell_value(rowx=0, colx=col))
        self.raw_table.append(self.fieldnames)
        for row in range(1, sh.nrows):
            context = {}
            r = []
            for col in range(sh.ncols):
                value = str(sh.cell_value(rowx=row, colx=col))
                context[self.fieldnames[col]] = value
                r.append(value)
            self.contexts.append(context)
            self.raw_table.append(r)

    def load_data(self, datafile):
        if datafile.name.lower().endswith('.csv'):
            self.load_csv(datafile, ',')
        elif datafile.name.lower().endswith('.xls') or datafile.name.lower().endswith('.xlsx'):
            self.load_excel(datafile)
        else:
            raise TemplateTypeNotSupported

    # Looking for missing variables/fields used in csv file and template and print summary
    def verify_template_odt(self, template):
        messages = []
        test_string = "a"
        renderer = CustomOdtRenderer()
        no_params = renderer.render_content_to_xml(template)
        # check if each of the fields in csv file exist in template
        for field in self.fieldnames:
            w_param = renderer.render_content_to_xml(template, **{field: test_string})
            if w_param == no_params:
                messages.append("'{}' not defined in the template".format(field))
        # check if any field(s) used in the template is not defined in the csv
        parse_content = Environment().parse(renderer.content_original)
        undeclared_template_variables = meta.find_undeclared_variables(parse_content)
        for variable in undeclared_template_variables:
            if variable not in self.fieldnames:
                messages.append("'{}' not defined in the csv".format(variable))
        return messages

    # render the output files
    def render_output_odt(self, template, output_name_template):
        r_result = RenderResult()
        for cont in self.contexts:
            renderer = CustomOdtRenderer()
            output = io.BytesIO()
            doc = renderer.render(template, **cont)
            output.write(doc)
            r_result.files[re.sub(r'[\\/:*?\"<>|]','',Template(output_name_template).render(cont)) + ".odt"] = output
        return r_result


    # Looking for missing variables/fields used in csv file and template and print summary
    def verify_template_docx(self, template):
        messages = []
        test_string = "a"
        doc = DocxTemplate(template)
        doc.render({})
        no_params = doc.get_xml()
        # check if each of the fields in csv file exist in template
        for field in self.fieldnames:
            doc = DocxTemplate(template)
            doc.render({field: test_string})
            if doc.get_xml() == no_params:
                messages.append("'{}' not defined in the template".format(field))
        # check if any field(s) used in the template is not defined in the csv
        doc = DocxTemplate(template)
        for variable in doc.get_undeclared_template_variables():
            if variable not in self.fieldnames:
                messages.append("'{}' not defined in the csv".format(variable))
        return messages

    # render the output files
    def render_output_docx(self, template, output_name_template):
        r_result = RenderResult()
        for cont in self.contexts:
            output = io.BytesIO()
            doc = DocxTemplate(template)
            doc.render(cont)
            doc.save(output)
            r_result.files[re.sub(r'[\\/:*?\"<>|]','',Template(output_name_template).render(cont)) + ".docx"] = output
        return r_result


    def verify(self, template):
        if template.name.lower().endswith('.docx'):
            return self.verify_template_docx(template)
        elif template.name.lower().endswith('.odt'):
            return self.verify_template_odt(template)
        else:
            raise TemplateTypeNotSupported

    
    def createArchive(self, result):
        archive = io.BytesIO()
        zf = zipfile.ZipFile(archive,mode='w',compression=zipfile.ZIP_DEFLATED)

        for filename in result.files:
            zf.writestr(filename, result.files[filename].getvalue())
        
        result.archive = archive

    def render(self, template, output_name_template):
        result = RenderResult()
        if template.name.lower().endswith('.docx'):
            result = self.render_output_docx(template, (output_name_template if output_name_template is not None else '{{ ' + self.fieldnames[0] + ' }}'))
        elif template.name.lower().endswith('.odt'):
            result = self.render_output_odt(template, (output_name_template if output_name_template is not None else '{{ ' + self.fieldnames[0] + ' }}'))
        else:
            raise TemplateTypeNotSupported
        self.createArchive(result)
        return result

