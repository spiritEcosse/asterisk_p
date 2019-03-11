from django.contrib.auth.views import logout_then_login, auth_login
from django.core.exceptions import PermissionDenied

class GroupRequiredMixin(object):
    """
        group_required - list of strings, required param
    """

    group_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return auth_login(request)

        if not bool(set(request.user.groups.values_list('name', flat=True)).intersection(self.group_required)):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
