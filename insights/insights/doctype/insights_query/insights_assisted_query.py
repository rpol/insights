# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from functools import cached_property

import frappe

from .utils import AssistedQuery, InsightsTable

DEFAULT_JSON = {
    "table": {},
    "joins": [],
    "columns": [],
    "calculations": [],
    "filters": [],
    "summarise": {},
    "order_by": [],
    "limit": None,
}


class InsightsAssistedQueryController:
    def __init__(self, doc):
        self.doc = doc
        if not frappe.parse_json(self.doc.json):
            self.doc.json = frappe.as_json(DEFAULT_JSON)

    def validate(self):
        pass

    @cached_property
    def query_json(self):
        return AssistedQuery.from_dict(frappe.parse_json(self.doc.json))

    def get_sql(self):
        return self.doc._data_source.build_query(self.doc, with_cte=True)

    def get_columns(self):
        return self.get_query_columns() or self.get_tables_columns()

    def get_query_columns(self):
        columns = []
        metrics = []
        dimensions = []

        for column in self.query_json.columns:
            columns.append(
                {
                    **column.column.__dict__,
                    "label": column.alias or column.column.label,
                }
            )

        if (
            not self.query_json.summarise
            or not self.query_json.summarise.metrics
            or not self.query_json.summarise.dimensions
        ):
            return columns

        for metric in self.query_json.summarise.metrics:
            if metric.aggregation.value != "count":
                metrics.append(
                    {
                        **metric.column.__dict__,
                        "label": metric.alias or metric.column.label,
                    }
                )
                continue
            metrics.append(
                frappe._dict(label="Count of Records", column="count", type="Integer")
            )

        for dimension in self.query_json.summarise.dimensions:
            dimensions.append(
                {
                    **dimension.column.__dict__,
                    "label": dimension.alias or dimension.column.label,
                    "format_options": dimension.format_options,
                }
            )

        return columns + dimensions + metrics

    def get_tables_columns(self):
        columns = []
        selected_tables = self.get_selected_tables()
        selected_tables_names = [t.get("table") for t in selected_tables]
        for table in set(selected_tables_names):
            table_doc = InsightsTable.get_doc(
                data_source=self.doc.data_source, table=table
            )
            table_columns = table_doc.get_columns()
            columns += [
                frappe._dict(
                    {
                        "data_source": self.doc.data_source,
                        "table_label": table_doc.label,
                        "table": table_doc.table,
                        "column": c.get("column"),
                        "label": c.get("label"),
                        "type": c.get("type"),
                    }
                )
                for c in table_columns
            ]
        return columns

    def get_selected_tables(self):
        if not self.query_json.table:
            return []
        tables = [self.query_json.table]
        join_tables = [join.right_table for join in self.query_json.joins]
        return tables + join_tables

    def before_fetch(self):
        if self.doc.data_source != "Query Store":
            return
        raise frappe.ValidationError(
            "Query Store data source is not supported for assisted query"
        )

    def after_fetch_results(self, results):
        return results
