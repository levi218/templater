import csv
from docxtpl import DocxTemplate
from jinja2 import Environment, Template, meta
# import argparse
# import sys
# import os.path
# from pathlib import Path
from .custom_exceptions import TemplateTypeNotSupported, OutputNameTemplateSyntax
from .custom_odt_renderer import CustomOdtRenderer
import re
# from tempfile import NamedTemporaryFile
import io
import zipfile
# defining global variables

class RenderResult(object):
    def __init__(self):
        self.files = {}
        self.archive = None


class TemplateRenderer(object):
    contexts = []
    fieldnames = []

    # Load data from csv file
    def load_csv(self, csvfile, delimiter):
        # open csv file and prepare context array
        # if not os.path.isfile(csv_path):
        #     raise FileNotFoundError("File {} not found".format(csv_path))
        # with open(csv_path, encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        self.fieldnames = reader.fieldnames
        for row in reader:
            context = {}
            for key, value in row.items():
                context[key] = value
            self.contexts.append(context)

                            
    # Looking for missing variables/fields used in csv file and template and print summary
    def verify_template_odt(self, template):
        # if not os.path.isfile(template_path):
        #     raise FileNotFoundError("File {} not found".format(template_path))
        messages = []
        test_string = "a"
        # print("Verifying template...")
        renderer = CustomOdtRenderer()
        # template = open(template_path, 'rb')
        no_params = renderer.render_content_to_xml(template)
        # check if each of the fields in csv file exist in template
        # print("Checking fields in csv")
        for field in self.fieldnames:
            # print("\tChecking '"+field + "'...")
            w_param = renderer.render_content_to_xml(template, **{field: test_string})
            if w_param == no_params:
                messages.append("'{}' not defined in the template".format(field))
                # counter+=1
            # else:
            #     print("\t\tOK")
        # check if any field(s) used in the template is not defined in the csv
        # print("Checking variables in template")
        parse_content = Environment().parse(renderer.content_original)
        undeclared_template_variables = meta.find_undeclared_variables(parse_content)
        for variable in undeclared_template_variables:
            # print("\tChecking '"+variable + "'...")
            if variable not in self.fieldnames:
                messages.append("'{}' not defined in the csv".format(variable))
                # counter+=1
            # else:
            #     print("\t\tOK")
        # return counter
        return messages

    # render the output files
    # def render_output_odt(template_path, output_name_template,output_dir):
    def render_output_odt(self, template, output_name_template):
        # if not os.path.isfile(template_path):
        #     raise FileNotFoundError("File {} not found".format(template_path))
        r_result = RenderResult()
        for cont in self.contexts:
            renderer = CustomOdtRenderer()
            # output = open((output_dir if output_dir is not None else '.' )+'/'+, 'wb');
            output = io.BytesIO()
            doc = renderer.render(template, **cont)
            output.write(doc)
            r_result.files[re.sub(r'[\\/:*?\"<>|]','',Template(output_name_template).render(cont)) + ".odt"] = output
        return r_result


    # Looking for missing variables/fields used in csv file and template and print summary
    # def verify_template_docx(template_path):
    def verify_template_docx(self, template):
        # if not os.path.isfile(template_path):
        #     raise FileNotFoundError("File {} not found".format(template_path))
        # counter = 0
        messages = []
        test_string = "a"
        # print("Verifying template...")
        doc = DocxTemplate(template)
        doc.render({})
        no_params = doc.get_xml()
        # check if each of the fields in csv file exist in template
        # print("Checking fields in csv")
        for field in self.fieldnames:
            doc = DocxTemplate(template)
            # print("\tChecking '"+field + "'...")
            doc.render({field: test_string})
            if doc.get_xml() == no_params:
                messages.append("'{}' not defined in the template".format(field))
                # counter+=1
            # else:
            #     print("\t\tOK")
        # check if any field(s) used in the template is not defined in the csv
        # print("Checking variables in template")
        doc = DocxTemplate(template)
        for variable in doc.get_undeclared_template_variables():
            # print("\tChecking '"+variable + "'...")
            if variable not in self.fieldnames:
                messages.append("'{}' not defined in the csv".format(variable))
                # counter+=1
            # else:
            #     print("\t\tOK")
        return messages

    # render the output files
    # def render_output_docx(template_path, output_name_template,output_dir):
    def render_output_docx(self, template, output_name_template):
        # if not os.path.isfile(template_path):
        #     raise FileNotFoundError("File {} not found".format(template_path))
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

    # def process(template_path, output_name_template, output_dir):
    def render(self, template, output_name_template):

        # if output_dir is not None:
        #     print('Creating output folder...')
        #     path = Path(output_dir)
        #     path.mkdir(parents=True, exist_ok=True)
        #     print("\tOK")
        result = RenderResult()
        if template.name.lower().endswith('.docx'):
            # print('Rendering files...')
            result = self.render_output_docx(template, (output_name_template if output_name_template is not None else '{{ ' + self.fieldnames[0] + ' }}'))
            # print("\tOK")
        elif template.name.lower().endswith('.odt'):
            # print('Rendering files...')
            result = self.render_output_odt(template, (output_name_template if output_name_template is not None else '{{ ' + self.fieldnames[0] + ' }}'))
        else:
            raise TemplateTypeNotSupported
        self.createArchive(result)
        return result

