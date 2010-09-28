from csc.conceptnet.models import *
from piston.handler import BaseHandler
from piston.doc import generate_doc
from csc.webapi import handlers

from django.test.client import Client
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import HttpResponse

from docutils.core import publish_string

API_BASE = 'http://openmind.media.mit.edu'

client = Client()
def documentation_view(request):
    docs = []
    for klass in handlers.__dict__.values():
        if isinstance(klass, type) and issubclass(klass, BaseHandler):
            doc = generate_doc(klass)
            if doc.get_resource_uri_template():
                doc.useful_methods = [m for m in doc.get_all_methods() if m.get_doc()]
                if hasattr(klass, 'example_args'):
                    args = klass.example_args
                    example_url = doc.get_resource_uri_template()
                    for arg, value in args.items():
                        example_url = example_url.replace('{%s}' % arg, str(value))
                    doc.example_url = example_url+'query.yaml'
                    doc.example_result = client.get(doc.example_url).content
                doc.uri_template = doc.get_resource_uri_template()
                docs.append(doc)
            elif hasattr(klass, 'example_uri'):
                doc = generate_doc(klass)
                example_url = klass.example_uri
                doc.example_url = example_url+'query.yaml'
                doc.example_result = client.get(doc.example_url).content
                doc.uri_template = klass.example_uri_template
                docs.append(doc)
    docs.sort(key=lambda doc: doc.uri_template)
    t = loader.get_template('documentation.txt')
    rst = t.render(Context({'docs': docs, 'API_BASE': API_BASE}))
    return HttpResponse(rst, mimetype='text/plain')
