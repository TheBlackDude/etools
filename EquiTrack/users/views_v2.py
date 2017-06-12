

from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError

from users.serializers import MinimalUserSerializer
from users.models import Office, Section
from .forms import ProfileForm
from .models import User, UserProfile, Country
from .serializers import (
    SimpleUserSerializer,
)


class UsersListApiView(ListAPIView):
    """
    Gets a list of Unicef Staff users in the current country.
    Country is determined by the currently logged in user.
    """
    model = User
    serializer_class = SimpleUserSerializer

    def get_queryset(self, pk=None):
        user = self.request.user
        queryset = self.model.objects.filter(profile__country=user.profile.country,
                                             is_staff=True).prefetch_related('profile',
                                                                             'groups',
                                                                             'user_permissions').order_by('first_name')
        user_ids = self.request.query_params.get("values", None)
        if user_ids:
            try:
                user_ids = [int(x) for x in user_ids.split(",")]
            except ValueError:
                raise ValidationError("Query parameter values are not integers")
            else:
                return self.model.objects.filter(
                    id__in=user_ids,
                    is_staff=True
                ).order_by('first_name')

        group = self.request.query_params.get("group", None)
        if group:
            queryset = queryset.filter(groups__name=group)

        return queryset

    def get_serializer_class(self):
        if self.request.query_params.get('verbosity', None) == 'minimal':
            return MinimalUserSerializer
        return super(UsersListApiView, self).get_serializer_class()

