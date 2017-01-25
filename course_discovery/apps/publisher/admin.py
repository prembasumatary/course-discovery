from django.contrib import admin
from guardian.admin import GuardedModelAdmin

from course_discovery.apps.publisher.forms import (
    UserAttributesAdminForm, CourseUserRoleForm, CourseRunAdminForm, OrganizationUserRoleForm
)
from course_discovery.apps.publisher.models import (
    Course, CourseRun, CourseUserRole, OrganizationExtension, OrganizationUserRole, Seat, State, UserAttributes
)


admin.site.register(Course)
admin.site.register(Seat)
admin.site.register(State)


@admin.register(CourseUserRole)
class CourseUserRoleAdmin(admin.ModelAdmin):
    form = CourseUserRoleForm


@admin.register(OrganizationExtension)
class OrganizationExtensionAdmin(GuardedModelAdmin):
    pass


@admin.register(UserAttributes)
class UserAttributesAdmin(admin.ModelAdmin):
    form = UserAttributesAdminForm


@admin.register(OrganizationUserRole)
class OrganizationUserRoleAdmin(admin.ModelAdmin):
    form = OrganizationUserRoleForm


@admin.register(CourseRun)
class CourseRunAdmin(admin.ModelAdmin):
    form = CourseRunAdminForm
    list_display = ('course', 'lms_course_id', 'state',)
