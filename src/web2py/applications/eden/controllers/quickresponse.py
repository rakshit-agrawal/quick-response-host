# -*- coding: utf-8 -*-

"""
    Quick Response Host Pages
"""

module = request.controller
resourcename = request.function

if not settings.has_module(module):
    raise HTTP(404, body="Module disabled: %s" % module)

s3db.hrm_vars()

# -----------------------------------------------------------------------------
def index():
    pass

def volunteer():
    """ Volunteers Controller """
    table = s3db.pr_person
    #print(table)
    #print(vars(table))


    if request.args:
        x= request.args[0]
        if x=="create":
            table = s3db.hrm_human_resource
        elif x=="list":
            table = s3db.pr_person

    form = SQLFORM(table)

    return dict(form=form)
