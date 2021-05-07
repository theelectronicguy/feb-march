from django.http import Http404
from django.views.generic import TemplateView


class EmailPreviewTemplateView(TemplateView):
    """
    The view for staff only to be able to preview email templates.
    Example:
        /emails/preview/?template=users/relationship-request-created.html&child_full_name=Alex%20Jansen
    """

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser and request.user.is_staff):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [f'emails/{self.request.GET["template"]}']

    def get_context_data(self, **kwargs):
        ctx = {}
        for key, value in self.request.GET.items():
            ctx[key] = value

        return super().get_context_data(**ctx)
