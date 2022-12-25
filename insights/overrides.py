# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

from insights.insights.doctype.insights_team.insights_team import (
    get_allowed_resources_for_user,
)


def has_permission(doc, ptype, user):
    if doc.doctype not in [
        "Insights Data Source",
        "Insights Table",
        "Insights Query",
        "Insights Dashboard",
    ]:
        return

    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return True

    allowed_resources = get_allowed_resources_for_user(doc.doctype, user)
    print(allowed_resources)
    if doc.name in allowed_resources:
        return True

    return False
