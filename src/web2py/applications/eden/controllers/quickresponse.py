# -*- coding: utf-8 -*-

"""
    Quick Response Host Pages
"""
import time

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

def createVolunteer():
    """ Volunteers Controller """
    exclude_fields = [
            'no_table_pe_label__row',
            'no_table_organisation_id__row',
            'no_table_site_id__row',
            'no_table_code__row',
            'no_table_job_title_id__row',
            'no_table_department_id__row',
            'no_table_essential__row',
            'no_table_start_date__row',
            'no_table_status__row',
            'no_table_preferred_name__row',
            'no_table_initials__row',
            'no_table_local_name__row',
            'no_table_site_contact__row']
    form = SQLFORM.factory(s3db.pr_person, s3db.hrm_human_resource)

    form.vars.organisation_id = 1
    form.vars.start_date = time.strftime("%m/%d/%Y") 
    if request.args:
        t = request.args[0]
        if t == 'firstAid':
            form.vars.job_title_id = 1
        elif t == 'techSupport':
            form.vars.job_title_id = 2
        elif t == 'leadVolunteer':
            form.vars.job_title_id = 3
            form.vars.essential = True
        elif t == 'generalVolunteer':
            form.vars.job_title_id = 4
    for row in form.components[0].elements('tr'):
        if row['_id'] in exclude_fields:
            row['_class'] = ' collapse'
        #if row['attributes']['_id'] in exclude_fields:
            #row['_class'] = 'collapse'
        #print(vars(row))
    showFields = DIV(A(SPAN('Show All Fields', _class="filter-advanced-label"), _class="filter-advanced", _id="showFields"), _class="filter-controls")
    form[0].insert(-1,showFields)
    form.process()
    return dict(form=form)

def volunteerCategories():
    """ Task Selection Controller """
    firstAidLink = A('First Aid', target='volunteerCategories', _class='btn btn-default btn-block btn-lg main-btn',  _role='button', _href='createVolunteer/firstAid')
    techSupport = A('Tech Support', target='volunteerSearch', _class='btn btn-default btn-block btn-lg main-btn', _role='button', _href='createVolunteer/techSupport')    
    leadVolunteer = A('Lead Volunteer', target='volunteerCategories', _class='btn btn-default btn-block btn-lg main-btn',  _role='button', _href='createVolunteer/leadVolunteer')
    generalVolunteer = A('List Volunteers', target='volunteerSearch', _class='btn btn-default btn-block btn-lg main-btn', _role='button', _href='createVolunteer/generalVolunteer')

    return dict(one=firstAidLink, two=techSupport, three=leadVolunteer, four=generalVolunteer)

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

def person():
    """
        Person Controller
        - used to see PR component tabs, for Personal Profile & Imports
        - includes components relevant to HRM
    """

    configure = s3db.configure
    set_method = s3db.set_method

    # Custom Method for Contacts
    set_method("pr", resourcename,
               method = "contacts",
               action = s3db.pr_Contacts)

    # Custom Method for CV
    set_method("pr", resourcename,
               method = "cv",
               action = s3db.hrm_CV)

    # Custom Method for HR Record
    set_method("pr", resourcename,
               method = "record",
               action = s3db.hrm_Record)

    if settings.has_module("asset"):
        # Assets as component of people
        s3db.add_components("pr_person", asset_asset="assigned_to_id")
        # Edits should always happen via the Asset Log
        # @ToDo: Allow this method too, if we can do so safely
        configure("asset_asset",
                  insertable = False,
                  editable = False,
                  deletable = False)

    group = get_vars.get("group", "volunteer")
    hr_id = get_vars.get("human_resource.id", None)
    if not str(hr_id).isdigit():
        hr_id = None

    # Configure human resource table
    table = s3db.hrm_human_resource
    table.type.default = 2
    get_vars["xsltmode"] = "volunteer"
    if hr_id:
        hr = db(table.id == hr_id).select(table.type,
                                          limitby=(0, 1)).first()
        if hr:
            group = hr.type == 2 and "volunteer" or "staff"
            # Also inform the back-end of this finding
            get_vars["group"] = group

    # Configure person table
    tablename = "pr_person"
    table = s3db[tablename]
    configure(tablename,
              deletable = False)

    mode = session.s3.hrm.mode
    if mode is not None:
        # Configure for personal mode
        s3db.hrm_human_resource.organisation_id.readable = True
        s3.crud_strings[tablename].update(
            title_display = T("Personal Profile"),
            title_update = T("Personal Profile"))
        # People can view their own HR data, but not edit it
        configure("hrm_human_resource",
                  insertable = False,
                  editable = False,
                  deletable = False)
        configure("hrm_certification",
                  insertable = True,
                  editable = True,
                  deletable = True)
        configure("hrm_credential",
                  insertable = False,
                  editable = False,
                  deletable = False)
        configure("hrm_competency",
                  insertable = True,  # Can add unconfirmed
                  editable = False,
                  deletable = False)
        configure("hrm_training",    # Can add but not provide grade
                  insertable = True,
                  editable = False,
                  deletable = False)
        configure("hrm_experience",
                  insertable = False,
                  editable = False,
                  deletable = False)
        configure("pr_group_membership",
                  insertable = False,
                  editable = False,
                  deletable = False)
    else:
        # Configure for HR manager mode
        s3.crud_strings[tablename].update(
                title_display = T("Volunteer Details"),
                title_update = T("Volunteer Details"),
                title_upload = T("Import Volunteers"),
                )

    # Upload for configuration (add replace option)
    s3.importerPrep = lambda: dict(ReplaceOption=T("Remove existing data before import"))

    # Import pre-process
    def import_prep(data, group=group):
        """
            Deletes all HR records (of the given group) of the organisation
            before processing a new data import, used for the import_prep
            hook in response.s3
        """
        resource, tree = data
        xml = current.xml
        tag = xml.TAG
        att = xml.ATTRIBUTE
        if s3.import_replace:
            if tree is not None:
                if group == "staff":
                    group = 1
                elif group == "volunteer":
                    group = 2
                else:
                    return # don't delete if no group specified

                root = tree.getroot()
                expr = "/%s/%s[@%s='org_organisation']/%s[@%s='name']" % \
                       (tag.root, tag.resource, att.name, tag.data, att.field)
                orgs = root.xpath(expr)
                for org in orgs:
                    org_name = org.get("value", None) or org.text
                    if org_name:
                        try:
                            org_name = json.loads(xml.xml_decode(org_name))
                        except:
                            pass
                    if org_name:
                        htable = s3db.hrm_human_resource
                        otable = s3db.org_organisation
                        query = (otable.name == org_name) & \
                                (htable.organisation_id == otable.id) & \
                                (htable.type == group)
                        resource = s3db.resource("hrm_human_resource", filter=query)
                        resource.delete(format="xml", cascade=True)
    s3.import_prep = import_prep

    # CRUD pre-process
    def prep(r):

        # Plug-in role matrix for Admins/OrgAdmins
        s3base.S3PersonRoleManager.set_method(r, entity="pr_person")

        if r.representation == "s3json":
            current.xml.show_ids = True
        elif r.interactive and r.method != "import":
            if not r.component:
                table = r.table
                # Assume volunteers only between 12-81
                table.date_of_birth.widget = S3DateWidget(past=972, future=-144)
                table.pe_label.readable = table.pe_label.writable = False
                table.missing.readable = table.missing.writable = False
                table.age_group.readable = table.age_group.writable = False

                s3db.pr_person_details.occupation.label = T("Normal Job")

                # Organisation Dependent Fields
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("pr_person", "middle_name")
                set_org_dependent_field("pr_person_details", "father_name")
                set_org_dependent_field("pr_person_details", "mother_name")
                set_org_dependent_field("pr_person_details", "affiliations")
                set_org_dependent_field("pr_person_details", "company")

            else:
                if r.component_name == "hours":
                    # Exclude records which are just to link to Programme
                    component_table = r.component.table
                    filter = (r.component.table.hours != None)
                    r.resource.add_component_filter("hours", filter)
                    component_table.training.readable = False
                    component_table.training_id.readable = False

                elif r.component_name == "physical_description":
                    # Hide all but those details that we want
                    # Lock all the fields
                    table = r.component.table
                    for field in table.fields:
                        table[field].writable = table[field].readable = False
                    # Now enable those that we want
                    table.ethnicity.writable = table.ethnicity.readable = True
                    table.blood_type.writable = table.blood_type.readable = True
                    table.medical_conditions.writable = table.medical_conditions.readable = True
                    table.other_details.writable = table.other_details.readable = True

                elif r.component_name == "asset":
                    # Edits should always happen via the Asset Log
                    # @ToDo: Allow this method too, if we can do so safely
                    configure("asset_asset",
                              insertable = False,
                              editable = False,
                              deletable = False)

                elif r.component_name == "group_membership":
                    s3db.hrm_configure_pr_group_membership()

            if r.method == "record" or r.component_name == "human_resource":
                table = s3db.hrm_human_resource
                table.code.writable = table.code.readable = False
                table.department_id.writable = table.department_id.readable = False
                table.essential.writable = table.essential.readable = False
                #table.location_id.readable = table.location_id.writable = True
                table.person_id.writable = table.person_id.readable = False
                table.site_id.writable = table.site_id.readable = False
                table.site_contact.writable = table.site_contact.readable = False
                org = session.s3.hrm.org
                field = table.organisation_id
                if org is None:
                    field.widget = None
                else:
                    field.default = org
                    field.readable = field.writable = False

                # Organisation Dependent Fields
                set_org_dependent_field = settings.set_org_dependent_field
                set_org_dependent_field("vol_details", "availability")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_type_id")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_id")
                set_org_dependent_field("vol_volunteer_cluster", "vol_cluster_position_id")

            resource = r.resource
            if mode is not None:
                r.resource.build_query(id=s3_logged_in_person())
            elif r.method not in ("deduplicate", "search_ac"):
                if not r.id and not hr_id:
                    # pre-action redirect => must retain prior errors
                    if response.error:
                        session.error = response.error
                    redirect(URL(r=r, f="volunteer"))
                if resource.count() == 1:
                    resource.load()
                    r.record = resource.records().first()
                    if r.record:
                        r.id = r.record.id
                if not r.record:
                    session.error = T("Record not found")
                    redirect(URL(f="volunteer",
                                 args=["search"]))
                if hr_id and r.component_name == "human_resource":
                    r.component_id = hr_id
                configure("hrm_human_resource",
                          insertable = False)

        elif r.component_name == "group_membership" and r.representation == "aadata":
            s3db.hrm_configure_pr_group_membership()

        return True
    s3.prep = prep

    # CRUD post-process
    def postp(r, output):
        if r.interactive and r.component:
            if r.component_name == "human_resource":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_human_resource_start_date','hrm_human_resource_end_date')''')
                vol_experience = settings.get_hrm_vol_experience()
                if vol_experience in ("programme", "both") and \
                   r.method not in ["search", "report", "import"] and \
                   "form" in output:
                    # Insert field to set the Programme
                    # @ToDo: Re-implement using http://eden.sahanafoundation.org/wiki/S3SQLForm
                    sep = ": "
                    table = s3db.hrm_programme_hours
                    field = table.programme_id
                    if r.id:
                        query = (table.person_id == r.id)
                        default = db(query).select(table.programme_id,
                                                   orderby=table.date).last()
                        if default:
                            default = default.programme_id
                    else:
                        default = field.default
                    widget = field.widget or SQLFORM.widgets.options.widget(field, default)
                    field_id = "%s_%s" % (table._tablename, field.name)
                    label = field.label
                    label = LABEL(label, label and sep, _for=field_id,
                                  _id=field_id + SQLFORM.ID_LABEL_SUFFIX)
                    row_id = field_id + SQLFORM.ID_ROW_SUFFIX
                    programme = s3_formstyle(row_id, label, widget,
                                             field.comment)
                    try:
                        output["form"][0].insert(2, programme[1])
                    except:
                        # A non-standard formstyle with just a single row
                        pass
                    try:
                        output["form"][0].insert(2, programme[0])
                    except:
                        pass

            elif r.component_name == "experience":
                # Set the minimum end_date to the same as the start_date
                s3.jquery_ready.append(
'''S3.start_end_date('hrm_experience_start_date','hrm_experience_end_date')''')
            elif r.component_name == "asset":
                # Provide a link to assign a new Asset
                # @ToDo: Proper Widget to do this inline
                output["add_btn"] = A(T("Assign Asset"),
                                      _href=URL(c="asset", f="asset"),
                                      _id="add-btn",
                                      _class="action-btn")
        return output
    s3.postp = postp

    # REST Interface
    if session.s3.hrm.orgname and mode is None:
        orgname = session.s3.hrm.orgname
    else:
        orgname = None

    return s3_rest_controller("pr", resourcename,
                              csv_template = ("hrm", "volunteer"),
                              csv_stylesheet = ("hrm", "person.xsl"),
                              csv_extra_fields = [
                                  dict(label="Type",
                                       field=s3db.hrm_human_resource.type)
                                                ],
                              orgname = orgname,
                              replace_option = T("Remove existing data before import"),
                              rheader = s3db.hrm_rheader,
                              )

