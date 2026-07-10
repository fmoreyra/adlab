"""
Admin views for veterinarian approval and pending-approval screen settings.
"""

from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView, View

from accounts.forms_veterinarian_admin import (
    AdminVeterinarianSearchForm,
    VeterinarianPendingApprovalSettingsForm,
)
from accounts.mixins import AdminRequiredMixin, VeterinarianRequiredMixin
from accounts.models import Veterinarian, VeterinarianPendingApprovalSettings
from accounts.services.veterinarian_approval_service import (
    VeterinarianApprovalService,
    can_delete,
    get_veterinarians_queryset,
    search_veterinarians,
)
from accounts.services.veterinarian_pending_settings_service import (
    warm_pending_settings_cache,
)
from pages.services.dashboard_announcement_service import render_message_safe

ADMIN_VET_PAGE_SIZE = 20


class VeterinarianPendingApprovalView(VeterinarianRequiredMixin, TemplateView):
    """
    Contact screen shown when a veterinarian tries to create protocols
    without admin approval.
    """

    template_name = "accounts/veterinarian_pending_approval.html"

    def get_context_data(self, **kwargs):
        """Load cached pending-approval screen content."""
        from accounts.services.veterinarian_pending_settings_service import (
            get_cached_pending_settings,
        )

        context = super().get_context_data(**kwargs)
        context["screen"] = get_cached_pending_settings()
        context["veterinarian"] = self.request.user.veterinarian_profile
        return context


class VeterinarianPendingApprovalSettingsEditView(
    AdminRequiredMixin, FormView
):
    """
    Admin-only view to edit the veterinarian pending-approval screen.
    """

    form_class = VeterinarianPendingApprovalSettingsForm
    template_name = "accounts/veterinarian_pending_settings_edit.html"
    success_url = reverse_lazy("pages:dashboard_admin")

    def get_initial(self):
        """Load current singleton values into the form."""
        settings_obj = VeterinarianPendingApprovalSettings.get_singleton()
        return {
            "title": settings_obj.title,
            "message": settings_obj.message,
            "contact_phone": settings_obj.contact_phone,
            "contact_email": settings_obj.contact_email,
            "is_active": settings_obj.is_active,
        }

    def get_context_data(self, **kwargs):
        """Add preview HTML and settings metadata to context."""
        context = super().get_context_data(**kwargs)
        settings_obj = VeterinarianPendingApprovalSettings.get_singleton()
        preview_html = ""

        if self.request.method == "POST":
            action = self.request.POST.get("action", "save")
            if action == "preview":
                form = self.get_form()
                if form.is_valid():
                    preview_html = render_message_safe(
                        form.cleaned_data.get("message", "")
                    )
        elif settings_obj.message.strip():
            preview_html = render_message_safe(settings_obj.message)

        context["preview_html"] = preview_html
        context["settings_obj"] = settings_obj
        return context

    def post(self, request, *args, **kwargs):
        """Handle preview without saving."""
        if request.POST.get("action") == "preview":
            form = self.get_form()
            if form.is_valid():
                return self.render_to_response(
                    self.get_context_data(form=form)
                )
            return self.form_invalid(form)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Save settings and refresh cache."""
        VeterinarianPendingApprovalSettings.update_settings(
            title=form.cleaned_data["title"],
            message=form.cleaned_data.get("message", ""),
            contact_phone=form.cleaned_data.get("contact_phone", ""),
            contact_email=form.cleaned_data.get("contact_email", ""),
            is_active=form.cleaned_data.get("is_active", False),
            user=self.request.user,
        )

        def _after_commit():
            warm_pending_settings_cache()

        transaction.on_commit(_after_commit)

        messages.success(
            self.request,
            "Pantalla de habilitación pendiente guardada correctamente.",
        )
        return super().form_valid(form)


class AdminVeterinarianManagementView(AdminRequiredMixin, View):
    """
    Admin panel for searching, approving, and removing veterinarian accounts.
    """

    template_name = "accounts/admin_veterinarian_management.html"

    def get(self, request):
        """Show search form and paginated veterinarian list."""
        form = AdminVeterinarianSearchForm(request.GET or None)
        return render(
            request,
            self.template_name,
            self._build_context(request, form),
        )

    def post(self, request):
        """Process approve, delete, or reactivate actions."""
        action = request.POST.get("action")
        veterinarian_id = request.POST.get("veterinarian_id")

        if action and veterinarian_id:
            return self._handle_action(request, action, veterinarian_id)

        form = AdminVeterinarianSearchForm(request.POST)
        return render(
            request,
            self.template_name,
            self._build_context(request, form),
        )

    def _handle_action(self, request, action, veterinarian_id):
        """Execute a row action and redirect back to the list."""
        veterinarian = get_object_or_404(Veterinarian, pk=veterinarian_id)
        service = VeterinarianApprovalService()
        status = request.GET.get("status", "pending")
        query = request.GET.get("query", "")

        if action == "approve":
            notes = (request.POST.get("notes") or "").strip()
            result = service.approve(
                veterinarian,
                request.user,
                request,
                notes=notes,
            )
        elif action == "delete":
            if request.POST.get("confirm_delete") != "on":
                messages.error(
                    request,
                    "Debe confirmar que entiende que la acción no se puede "
                    "des hacer.",
                )
                return redirect(self._list_url(status, query))

            allowed, mode, reason = can_delete(veterinarian)
            if not allowed:
                messages.error(request, reason)
                return redirect(self._list_url(status, query))

            if mode == "deactivate_only":
                messages.warning(request, reason)

            result = service.delete_account(
                veterinarian,
                request.user,
                request,
            )
        elif action == "reactivate":
            result = service.reactivate(
                veterinarian,
                request.user,
                request,
            )
        else:
            messages.error(request, "Acción no reconocida.")
            return redirect(self._list_url(status, query))

        if result.success:
            messages.success(request, result.message)
        else:
            messages.error(request, result.message)

        return redirect(self._list_url(status, query))

    def _list_url(self, status, query):
        """Build redirect URL preserving list filters."""
        from django.urls import reverse

        url = reverse("pages:admin_veterinarian_management")
        params = []
        if status:
            params.append(f"status={status}")
        if query:
            params.append(f"query={query}")
        if params:
            return f"{url}?{'&'.join(params)}"
        return url

    def _build_context(self, request, form):
        """Build template context with paginated veterinarian results."""
        status = "pending"
        query = ""

        if form.is_valid():
            status = form.cleaned_data.get("status") or "pending"
            query = (form.cleaned_data.get("query") or "").strip()
        elif request.GET.get("status"):
            status = request.GET.get("status")

        queryset = search_veterinarians(
            get_veterinarians_queryset(status),
            query,
        )
        paginator = Paginator(queryset, ADMIN_VET_PAGE_SIZE)
        page_number = request.GET.get("page", 1)

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        veterinarians_with_meta = []
        for vet in page_obj.object_list:
            allowed, mode, delete_reason = can_delete(vet)
            veterinarians_with_meta.append(
                {
                    "veterinarian": vet,
                    "can_delete": allowed,
                    "delete_mode": mode,
                    "delete_reason": delete_reason,
                    "is_anonymized": vet.user.email.endswith("@invalid.local"),
                }
            )

        return {
            "form": form,
            "page_obj": page_obj,
            "veterinarians": veterinarians_with_meta,
            "is_search": bool(query),
            "total_count": paginator.count,
            "current_status": status,
            "current_query": query,
        }
