from django.urls import path

from protocols import views, views_reports, views_workorder

app_name = "protocols"

urlpatterns = [
    # List and create
    path("", views.protocol_list_view, name="protocol_list"),
    path(
        "select-type/",
        views.protocol_select_type_view,
        name="protocol_select_type",
    ),
    path(
        "create/cytology/",
        views.protocol_create_cytology_view,
        name="protocol_create_cytology",
    ),
    path(
        "create/histopathology/",
        views.protocol_create_histopathology_view,
        name="protocol_create_histopathology",
    ),
    # Detail, edit, delete
    path("<int:pk>/", views.protocol_detail_view, name="protocol_detail"),
    path("public/<uuid:external_id>/", views.protocol_public_detail_view, name="protocol_public_detail"),
    path("<int:pk>/edit/", views.protocol_edit_view, name="protocol_edit"),
    path(
        "<int:pk>/delete/", views.protocol_delete_view, name="protocol_delete"
    ),
    path(
        "<int:pk>/submit/", views.protocol_submit_view, name="protocol_submit"
    ),
    # Reception (laboratory staff only)
    path("reception/", views.reception_search_view, name="reception_search"),
    path(
        "reception/<int:pk>/confirm/",
        views.reception_confirm_view,
        name="reception_confirm",
    ),
    path(
        "reception/<int:pk>/detail/",
        views.reception_detail_view,
        name="reception_detail",
    ),
    path(
        "reception/<int:pk>/label/",
        views.reception_label_pdf_view,
        name="reception_label",
    ),
    path(
        "reception/pending/",
        views.reception_pending_view,
        name="reception_pending",
    ),
    path(
        "reception/history/",
        views.reception_history_view,
        name="reception_history",
    ),
    # Processing (Step 05 - laboratory staff only)
    path(
        "processing/",
        views.processing_dashboard_view,
        name="processing_dashboard",
    ),
    path(
        "processing/queue/",
        views.processing_queue_view,
        name="processing_queue",
    ),
    path(
        "processing/protocol/<int:pk>/",
        views.protocol_processing_status_view,
        name="processing_status",
    ),
    path(
        "processing/cassette/create/<int:protocol_pk>/",
        views.cassette_create_view,
        name="cassette_create",
    ),
    path(
        "processing/slide/register/<int:protocol_pk>/",
        views.slide_register_view,
        name="slide_register",
    ),
    path(
        "processing/slide/<int:slide_pk>/stage/",
        views.slide_update_stage_view,
        name="slide_update_stage",
    ),
    path(
        "processing/slide/<int:slide_pk>/quality/",
        views.slide_update_quality_view,
        name="slide_update_quality",
    ),
    # Reports
    path(
        "reports/pending/",
        views_reports.report_pending_list_view,
        name="report_pending_list",
    ),
    path(
        "reports/history/",
        views_reports.report_history_view,
        name="report_history",
    ),
    path(
        "reports/create/<int:protocol_id>/",
        views_reports.report_create_view,
        name="report_create",
    ),
    path(
        "reports/<int:pk>/edit/",
        views_reports.report_edit_view,
        name="report_edit",
    ),
    path(
        "reports/<int:pk>/",
        views_reports.report_detail_view,
        name="report_detail",
    ),
    path(
        "reports/<int:pk>/finalize/",
        views_reports.report_finalize_view,
        name="report_finalize",
    ),
    path(
        "reports/<int:pk>/pdf/",
        views_reports.report_pdf_view,
        name="report_pdf",
    ),
    path(
        "reports/<int:pk>/send/",
        views_reports.report_send_view,
        name="report_send",
    ),
    # Work Orders (Step 07)
    path(
        "workorders/",
        views_workorder.workorder_list_view,
        name="workorder_list",
    ),
    path(
        "workorders/pending/",
        views_workorder.workorder_pending_protocols_view,
        name="workorder_pending_protocols",
    ),
    path(
        "workorders/select/<int:veterinarian_id>/",
        views_workorder.workorder_select_protocols_view,
        name="workorder_select_protocols",
    ),
    path(
        "workorders/create/<str:protocol_ids>/",
        views_workorder.workorder_create_view,
        name="workorder_create_with_protocols",
    ),
    path(
        "workorders/<int:pk>/",
        views_workorder.workorder_detail_view,
        name="workorder_detail",
    ),
    path(
        "workorders/<int:pk>/issue/",
        views_workorder.workorder_issue_view,
        name="workorder_issue",
    ),
    path(
        "workorders/<int:pk>/send/",
        views_workorder.workorder_send_view,
        name="workorder_send",
    ),
    path(
        "workorders/<int:pk>/pdf/",
        views_workorder.workorder_pdf_view,
        name="workorder_pdf",
    ),
]
