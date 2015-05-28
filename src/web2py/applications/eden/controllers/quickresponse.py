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
    """ Dashboard """

    mode = session.s3.hrm.mode
    if mode is not None:
        # Go to Personal Profile
        redirect(URL(f="person"))
    else:
        # Bypass home page & go direct to Volunteers Summary
        redirect(URL(f="volunteerSearch"))

def volunteerDetails():
    """ Volunteers Controller """
    table = s3db.pr_person

    if request.args:
        x= request.args[0]
        if x=="create":
            table = s3db.hrm_human_resource
        elif x=="list":
            table = s3db.pr_person

    form = SQLFORM(table)

    return dict(form=form)

def volunteerCategories():
    """ Task Selection Controller """
    task1 = "First Aid"
    task2 = "Tech Support"
    task3 = "Leader Volunteer"
    task4 = "General Volunteer"
    link1 = A('click me', callback="#", target="t")
    return dict(task1=task1, task2=task2, task3= task3, task4=task4, link1=link1)

def volunteerSearch():
    """ Volunteers Controller """

    # Volunteers only
    s3.filter = FS("type") == 2

    vol_experience = settings.get_hrm_vol_experience()

    def prep(r):
        resource = r.resource
        get_config = resource.get_config

        # CRUD String
        s3.crud_strings[resource.tablename] = s3.crud_strings["hrm_volunteer"]

        # Default to volunteers
        table = r.table
        table.type.default = 2

        # Volunteers use home address
        location_id = table.location_id
        location_id.label = T("Home Address")

        # Configure list_fields
        if r.representation == "xls":
            # Split person_id into first/middle/last to
            # make it match Import sheets
            list_fields = ["person_id$first_name",
                           "person_id$middle_name",
                           "person_id$last_name",
                           ]
        else:
            list_fields = ["person_id",
                           ]
        list_fields.append("job_title_id")
        if settings.get_hrm_multiple_orgs():
            list_fields.append("organisation_id")
        list_fields.extend(((settings.get_ui_label_mobile_phone(), "phone.value"),
                            (T("Email"), "email.value"),
                            "location_id",
                            ))
        if settings.get_hrm_use_trainings():
            list_fields.append((T("Trainings"),"person_id$training.course_id"))
        if settings.get_hrm_use_certificates():
            list_fields.append((T("Certificates"),"person_id$certification.certificate_id"))

        # Volunteer Programme and Active-status
        report_options = get_config("report_options")
        if vol_experience in ("programme", "both"):
            # Don't use status field
            table.status.readable = table.status.writable = False
            # Use active field?
            vol_active = settings.get_hrm_vol_active()
            if vol_active:
                list_fields.insert(3, (T("Active?"), "details.active"))
            # Add Programme to List Fields
            list_fields.insert(6, "person_id$hours.programme_id")

            # Add active and programme to Report Options
            report_fields = report_options.rows
            report_fields.append("person_id$hours.programme_id")
            if vol_active:
                report_fields.append((T("Active?"), "details.active"))
            report_options.rows = report_fields
            report_options.cols = report_fields
            report_options.fact = report_fields
        else:
            # Use status field
            list_fields.append("status")

        # Update filter widgets
        filter_widgets = \
            s3db.hrm_human_resource_filters(resource_type="volunteer",
                                            hrm_type_opts=s3db.hrm_type_opts)

        # Reconfigure
        resource.configure(list_fields = list_fields,
                           filter_widgets = filter_widgets,
                           report_options = report_options,
                           )

        if r.interactive:
            if r.id:
                if r.method not in ("profile", "delete"):
                    # Redirect to person controller
                    vars = {"human_resource.id": r.id,
                            "group": "volunteer"
                            }
                    if r.representation == "iframe":
                        vars["format"] = "iframe"
                        args = [r.method]
                    else:
                        args = []
                    redirect(URL(f="person", vars=vars, args=args))
            else:
                if r.method == "import":
                    # Redirect to person controller
                    redirect(URL(f="person",
                                 args="import",
                                 vars={"group": "volunteer"}))

                elif not r.component and r.method != "delete":
                    # Configure AddPersonWidget
                    table.person_id.widget = S3AddPersonWidget2(controller="vol")
                    # Show location ID
                    location_id.writable = location_id.readable = True
                    # Hide unwanted fields
                    for fn in ("site_id",
                               "code",
                               "department_id",
                               "essential",
                               "site_contact",
                               "status",
                               ):
                        table[fn].writable = table[fn].readable = False
                    # Organisation Dependent Fields
                    set_org_dependent_field = settings.set_org_dependent_field
                    set_org_dependent_field("pr_person_details", "father_name")
                    set_org_dependent_field("pr_person_details", "mother_name")
                    set_org_dependent_field("pr_person_details", "affiliations")
                    set_org_dependent_field("pr_person_details", "company")
                    set_org_dependent_field("vol_details", "availability")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_type_id")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_id")
                    set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_position_id")
                    # Label for "occupation"
                    s3db.pr_person_details.occupation.label = T("Normal Job")
                    # Assume volunteers only between 12-81
                    s3db.pr_person.date_of_birth.widget = S3DateWidget(past=972, future=-144)
        return True
    s3.prep = prep

    def postp(r, output):
        if r.interactive and not r.component:
            # Set the minimum end_date to the same as the start_date
            s3.jquery_ready.append(
'''S3.start_end_date('hrm_human_resource_start_date','hrm_human_resource_end_date')''')

            # Configure action buttons
            s3_action_buttons(r, deletable=settings.get_hrm_deletable())
            if "msg" in settings.modules and \
               settings.get_hrm_compose_button() and \
               auth.permission.has_permission("update", c="hrm", f="compose"):
                # @ToDo: Remove this now that we have it in Events?
                s3.actions.append({
                        "url": URL(f="compose",
                                    vars = {"human_resource.id": "[id]"}),
                        "_class": "action-btn send",
                        "label": str(T("Send Message"))
                    })

            # Insert field to set the Programme
            if vol_experience in ("programme", "both") and \
               r.method not in ("search", "report", "import") and \
               "form" in output:
                # @ToDo: Re-implement using
                # http://eden.sahanafoundation.org/wiki/S3SQLForm
                # NB This means adjusting IFRC/config.py too
                sep = ": "
                table = s3db.hrm_programme_hours
                field = table.programme_id
                default = field.default
                widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                field_id = "%s_%s" % (table._tablename, field.name)
                label = field.label
                row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                if s3_formstyle == "bootstrap":
                    label = LABEL(label, label and sep, _class="control-label", _for=field_id)
                    _controls = DIV(widget, _class="controls")
                    row = DIV(label, _controls,
                                _class="control-group",
                                _id=row_id,
                                )
                    output["form"][0].insert(4, row)
                elif callable(s3_formstyle):
                    label = LABEL(label, label and sep, _for=field_id,
                                    _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                    programme = s3_formstyle(row_id, label, widget,
                                                field.comment)
                    if isinstance(programme, DIV) and \
                       "form-row" in programme["_class"]:
                        # Foundation formstyle
                        output["form"][0].insert(4, programme)
                    else:
                        try:
                            output["form"][0].insert(4, programme[1])
                        except:
                            # A non-standard formstyle with just a single row
                            pass
                        try:
                            output["form"][0].insert(4, programme[0])
                        except:
                            pass
                else:
                    # Unsupported
                    raise
        elif r.representation == "plain":
            # Map Popups
            output = s3db.hrm_map_popup(r)
        return output
    s3.postp = postp


    #for i in s3_rest_controller("hrm", "human_resource")['r'].keys():
    #    print(i + ':  ', s3_rest_controller("hrm", "human_resource")['r'].get(i))
    controller = s3_rest_controller("hrm", "human_resource")
    print(controller)
    response.view = "quickresponse/volunteerSearch.html"
    return controller 

def volunteerAddOrSearch():
    addLink = A('Add Volunteer', target='volunteerCategories', _class='btn btn-default btn-block btn-lg main-btn',  _role='button', _href='volunteerCategories')
    listLink = A('List Volunteers', target='volunteerSearch', _class='btn btn-default btn-block btn-lg main-btn', _role='button', _href='volunteerSearch')    
    return dict(addLink=addLink, listLink=listLink)
