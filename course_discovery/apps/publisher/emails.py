import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail.message import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from opaque_keys.edx.keys import CourseKey

from course_discovery.apps.publisher.choices import PublisherUserRole
from course_discovery.apps.publisher.utils import is_email_notification_enabled

logger = logging.getLogger(__name__)


def send_email_for_studio_instance_created(course_run, updated_text=_('created')):
    """ Send an email to course team on studio instance creation.

        Arguments:
            course_run (CourseRun): CourseRun object
            updated_text (String): String object
    """
    try:
        object_path = reverse('publisher:publisher_course_run_detail', kwargs={'pk': course_run.id})
        subject = _('Studio instance {updated_text}').format(updated_text=updated_text)     # pylint: disable=no-member

        to_addresses = [course_run.course.course_team_admin.email]
        from_address = settings.PUBLISHER_FROM_EMAIL

        course_team_admin = course_run.course.course_team_admin
        project_coordinator = course_run.course.project_coordinator

        context = {
            'updated_text': updated_text,
            'course_run': course_run,
            'course_run_page_url': 'https://{host}{path}'.format(
                host=Site.objects.get_current().domain.strip('/'), path=object_path
            ),
            'course_name': course_run.course.title,
            'from_address': from_address,
            'course_team_name': course_team_admin.get_full_name() or course_team_admin.username,
            'project_coordinator_name': project_coordinator.get_full_name() or project_coordinator.username,
            'contact_us_email': project_coordinator.email
        }

        txt_template_path = 'publisher/email/studio_instance_created.txt'
        html_template_path = 'publisher/email/studio_instance_created.html'

        txt_template = get_template(txt_template_path)
        plain_content = txt_template.render(context)
        html_template = get_template(html_template_path)
        html_content = html_template.render(context)
        email_msg = EmailMultiAlternatives(subject, plain_content, from_address, to=to_addresses)
        email_msg.attach_alternative(html_content, 'text/html')
        email_msg.send()
    except Exception:  # pylint: disable=broad-except
        error_message = 'Failed to send email notifications for course_run [{run_id}]'.format(run_id=course_run.id)
        logger.exception(error_message)
        raise Exception(error_message)


def send_email_for_course_creation(course, course_run):
    """ Send the emails for a course creation.

        Arguments:
            course (Course): Course object
            course_run (CourseRun): CourseRun object
    """
    txt_template = 'publisher/email/course_created.txt'
    html_template = 'publisher/email/course_created.html'

    subject = _('New Studio instance request for {title}').format(title=course.title)  # pylint: disable=no-member
    project_coordinator = course.project_coordinator
    course_team = course.course_team_admin

    if is_email_notification_enabled(project_coordinator):
        try:
            to_addresses = [project_coordinator.email]
            from_address = settings.PUBLISHER_FROM_EMAIL

            context = {
                'course_title': course.title,
                'date': course_run.created.strftime("%B %d, %Y"),
                'time': course_run.created.strftime("%H:%M:%S"),
                'course_team_name': course_team.get_full_name(),
                'project_coordinator_name': project_coordinator.get_full_name(),
                'dashboard_url': 'https://{host}{path}'.format(
                    host=Site.objects.get_current().domain.strip('/'), path=reverse('publisher:publisher_dashboard')
                ),
                'from_address': from_address,
                'contact_us_email': project_coordinator.email
            }

            template = get_template(txt_template)
            plain_content = template.render(context)
            template = get_template(html_template)
            html_content = template.render(context)

            email_msg = EmailMultiAlternatives(
                subject, plain_content, from_address, to=to_addresses
            )
            email_msg.attach_alternative(html_content, 'text/html')
            email_msg.send()
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                'Failed to send email notifications for creation of course [%s]', course_run.course.id
            )


def send_email_for_send_for_review(course, user):
    """ Send email when course is submitted for review.

        Arguments:
            course (Object): Course object
            user (Object): User object
    """
    txt_template = 'publisher/email/course/send_for_review.txt'
    html_template = 'publisher/email/course/send_for_review.html'
    subject = _('Review requested: {title}').format(title=course.title)  # pylint: disable=no-member

    try:
        recipient_user = course.marketing_reviewer
        user_role = course.course_user_roles.get(user=user)
        if user_role.role == PublisherUserRole.MarketingReviewer:
            recipient_user = course.course_team_admin

        page_path = reverse('publisher:publisher_course_detail', kwargs={'pk': course.id})
        context = {
            'course_name': course.title,
            'sender_team': 'course team' if user_role.role == PublisherUserRole.CourseTeam else 'marketing team',
            'page_url': 'https://{host}{path}'.format(
                host=Site.objects.get_current().domain.strip('/'), path=page_path
            )
        }

        send_course_workflow_email(course, user, subject, txt_template, html_template, context, recipient_user)
    except Exception:  # pylint: disable=broad-except
        logger.exception('Failed to send email notifications send for review of course %s', course.id)


def send_email_for_mark_as_reviewed(course, user):
    """ Send email when course is marked as reviewed.

        Arguments:
            course (Object): Course object
            user (Object): User object
    """
    txt_template = 'publisher/email/course/mark_as_reviewed.txt'
    html_template = 'publisher/email/course/mark_as_reviewed.html'
    subject = _('Review complete: {title}').format(title=course.title)  # pylint: disable=no-member

    try:
        recipient_user = course.marketing_reviewer
        user_role = course.course_user_roles.get(user=user)
        if user_role.role == PublisherUserRole.MarketingReviewer:
            recipient_user = course.course_team_admin

        page_path = reverse('publisher:publisher_course_detail', kwargs={'pk': course.id})
        context = {
            'course_name': course.title,
            'sender_team': 'course team' if user_role.role == PublisherUserRole.CourseTeam else 'marketing team',
            'page_url': 'https://{host}{path}'.format(
                host=Site.objects.get_current().domain.strip('/'), path=page_path
            )
        }

        send_course_workflow_email(course, user, subject, txt_template, html_template, context, recipient_user)
    except Exception:  # pylint: disable=broad-except
        logger.exception('Failed to send email notifications mark as reviewed of course %s', course.id)


def send_course_workflow_email(course, user, subject, txt_template, html_template, context, recipient_user):
    """ Send email for course workflow state change.

        Arguments:
            course (Object): Course object
            user (Object): User object
            subject (String): Email subject
            txt_template: (String): Email text template path
            html_template: (String): Email html template path
            context: (Dict): Email template context
            recipient_user: (Object): User object
    """

    if is_email_notification_enabled(recipient_user):
        project_coordinator = course.project_coordinator
        to_addresses = [recipient_user.email]
        from_address = settings.PUBLISHER_FROM_EMAIL

        course_page_path = reverse('publisher:publisher_course_detail', kwargs={'pk': course.id})

        context.update(
            {
                'recipient_name': recipient_user.full_name or recipient_user.username if recipient_user else '',
                'sender_name': user.full_name or user.username,
                'org_name': course.organizations.all().first().name,
                'contact_us_email': project_coordinator.email if project_coordinator else '',
                'course_page_url': 'https://{host}{path}'.format(
                    host=Site.objects.get_current().domain.strip('/'), path=course_page_path
                )
            }
        )

        template = get_template(txt_template)
        plain_content = template.render(context)
        template = get_template(html_template)
        html_content = template.render(context)

        email_msg = EmailMultiAlternatives(
            subject, plain_content, from_address, to_addresses
        )
        email_msg.attach_alternative(html_content, 'text/html')
        email_msg.send()


def send_email_for_send_for_review_course_run(course_run, user):
    """ Send email when course-run is submitted for review.

        Arguments:
            course-run (Object): CourseRun object
            user (Object): User object
    """
    course = course_run.course
    course_key = CourseKey.from_string(course_run.lms_course_id)
    txt_template = 'publisher/email/course_run/send_for_review.txt'
    html_template = 'publisher/email/course_run/send_for_review.html'
    subject = _('Review requested: {title} {run_number}').format(  # pylint: disable=no-member
        title=course.title,
        run_number=course_key.run)

    try:
        recipient_user = course.project_coordinator
        user_role = course.course_user_roles.get(user=user)
        if user_role.role == PublisherUserRole.ProjectCoordinator:
            recipient_user = course.course_team_admin

        page_path = reverse('publisher:publisher_course_run_detail', kwargs={'pk': course_run.id})
        context = {
            'course_name': course.title,
            'run_number': course_key.run,
            'sender_team': 'course team' if user_role.role == PublisherUserRole.CourseTeam else 'project coordinators',
            'page_url': 'https://{host}{path}'.format(
                host=Site.objects.get_current().domain.strip('/'), path=page_path
            )
        }

        send_course_workflow_email(course, user, subject, txt_template, html_template, context, recipient_user)
    except Exception:  # pylint: disable=broad-except
        logger.exception('Failed to send email notifications send for review of course-run %s', course_run.id)


def send_email_for_mark_as_reviewed_course_run(course_run, user):
    """ Send email when course-run is marked as reviewed.

        Arguments:
            course_run (Object): CourseRun object
            user (Object): User object
    """
    txt_template = 'publisher/email/course_run/mark_as_reviewed.txt'
    html_template = 'publisher/email/course_run/mark_as_reviewed.html'
    course = course_run.course
    course_key = CourseKey.from_string(course_run.lms_course_id)
    subject = _('Review complete: {course_name} {run_number}').format(  # pylint: disable=no-member
        course_name=course.title,
        run_number=course_key.run
    )

    try:
        page_path = reverse('publisher:publisher_course_run_detail', kwargs={'pk': course_run.id})
        recipient_user = course.project_coordinator
        user_role = course.course_user_roles.get(user=user)
        if user_role.role == PublisherUserRole.ProjectCoordinator:
            recipient_user = course.course_team_admin

        context = {
            'course_name': course.title,
            'run_number': course_key.run,
            'sender_team': 'course team' if user_role.role == PublisherUserRole.CourseTeam else 'project coordinators',
            'page_url': 'https://{host}{path}'.format(
                host=Site.objects.get_current().domain.strip('/'), path=page_path
            )
        }

        send_course_workflow_email(course, user, subject, txt_template, html_template, context, recipient_user)
    except Exception:  # pylint: disable=broad-except
        logger.exception('Failed to send email notifications for mark as reviewed of course-run %s', course_run.id)


def send_email_to_publisher(course_run, user):
    """ Send email to publisher when course-run is marked as reviewed.

        Arguments:
            course_run (Object): CourseRun object
            user (Object): User object
    """
    txt_template = 'publisher/email/course_run/mark_as_reviewed.txt'
    html_template = 'publisher/email/course_run/mark_as_reviewed.html'

    course_key = CourseKey.from_string(course_run.lms_course_id)
    subject = _('Review complete: {course_name} {run_number}').format(  # pylint: disable=no-member
        course_name=course_run.course.title,
        run_number=course_key.run
    )

    recipient_user = course_run.course.publisher
    user_role = course_run.course.course_user_roles.get(user=user)
    sender_team = 'course team'
    if user_role.role == PublisherUserRole.MarketingReviewer:
        sender_team = 'marketing team'

    try:
        if is_email_notification_enabled(recipient_user):
            project_coordinator = course_run.course.project_coordinator
            to_addresses = [recipient_user.email]
            from_address = settings.PUBLISHER_FROM_EMAIL
            page_path = reverse('publisher:publisher_course_run_detail', kwargs={'pk': course_run.id})
            context = {
                'recipient_name': recipient_user.full_name or recipient_user.username if recipient_user else '',
                'sender_name': user.full_name or user.username,
                'course_name': course_run.course.title,
                'run_number': course_key.run,
                'org_name': course_run.course.organizations.all().first().name,
                'sender_team': sender_team,
                'contact_us_email': project_coordinator.email if project_coordinator else '',
                'page_url': 'https://{host}{path}'.format(
                    host=Site.objects.get_current().domain.strip('/'), path=page_path
                )
            }

            template = get_template(txt_template)
            plain_content = template.render(context)
            template = get_template(html_template)
            html_content = template.render(context)

            email_msg = EmailMultiAlternatives(
                subject, plain_content, from_address, to_addresses
            )
            email_msg.attach_alternative(html_content, 'text/html')
            email_msg.send()

    except Exception:  # pylint: disable=broad-except
        logger.exception('Failed to send email notifications for mark as reviewed of course-run %s', course_run.id)


def send_email_preview_accepted(course_run):
    """ Send email for preview approved to publisher and project coordinator.

        Arguments:
            course_run (Object): CourseRun object
    """
    txt_template = 'publisher/email/course_run/preview_accepted.txt'
    html_template = 'publisher/email/course_run/preview_accepted.html'

    course = course_run.course
    publisher_user = course.publisher

    try:
        if is_email_notification_enabled(publisher_user):
            course_key = CourseKey.from_string(course_run.lms_course_id)
            subject = _('Publication requested: {course_name} {run_number}').format(  # pylint: disable=no-member
                course_name=course.title,
                run_number=course_key.run)
            project_coordinator = course.project_coordinator
            to_addresses = [publisher_user.email]
            if is_email_notification_enabled(project_coordinator):
                to_addresses.append(project_coordinator.email)
            from_address = settings.PUBLISHER_FROM_EMAIL
            page_path = reverse('publisher:publisher_course_run_detail', kwargs={'pk': course_run.id})
            course_page_path = reverse('publisher:publisher_course_detail', kwargs={'pk': course_run.course.id})
            context = {
                'course_name': course.title,
                'run_number': course_key.run,
                'publisher_role_name': PublisherUserRole.Publisher,
                'course_team': course.course_team_admin,
                'org_name': course.organizations.all().first().name,
                'contact_us_email': project_coordinator.email if project_coordinator else '',
                'page_url': 'https://{host}{path}'.format(
                    host=Site.objects.get_current().domain.strip('/'), path=page_path
                ),
                'course_page_url': 'https://{host}{path}'.format(
                    host=Site.objects.get_current().domain.strip('/'), path=course_page_path
                )
            }
            template = get_template(txt_template)
            plain_content = template.render(context)
            template = get_template(html_template)
            html_content = template.render(context)

            email_msg = EmailMultiAlternatives(
                subject, plain_content, from_address, to=[from_address], bcc=to_addresses
            )
            email_msg.attach_alternative(html_content, 'text/html')
            email_msg.send()
    except Exception:  # pylint: disable=broad-except
        message = 'Failed to send email notifications for preview approved of course-run [{id}].'.format(
            id=course_run.id
        )
        logger.exception(message)
        raise Exception(message)


def send_email_preview_page_is_available(course_run):
    """ Send email for course preview available to course team.

        Arguments:
            course_run (Object): CourseRun object
    """
    txt_template = 'publisher/email/course_run/preview_available.txt'
    html_template = 'publisher/email/course_run/preview_available.html'
    course_team_user = course_run.course.course_team_admin

    try:
        if is_email_notification_enabled(course_team_user):
            course_key = CourseKey.from_string(course_run.lms_course_id)
            subject = _('Review requested: Preview for {course_name} {run_number}').format(     # pylint: disable=no-member
                course_name=course_run.course.title,
                run_number=course_key.run
            )
            to_addresses = [course_team_user.email]
            from_address = settings.PUBLISHER_FROM_EMAIL
            project_coordinator = course_run.course.project_coordinator
            page_path = reverse('publisher:publisher_course_run_detail', kwargs={'pk': course_run.id})
            course_page_path = reverse('publisher:publisher_course_detail', kwargs={'pk': course_run.course.id})
            context = {
                'sender_role': PublisherUserRole.Publisher,
                'recipient_name': course_team_user.get_full_name() or course_team_user.username,
                'course_name': course_run.course.title,
                'course_run_number': course_key.run,
                'preview_link': course_run.preview_url,
                'contact_us_email': project_coordinator.email if project_coordinator else '',
                'page_url': 'https://{host}{path}'.format(
                    host=Site.objects.get_current().domain.strip('/'), path=page_path
                ),
                'course_page_url': 'https://{host}{path}'.format(
                    host=Site.objects.get_current().domain.strip('/'), path=course_page_path
                ),
                'platform_name': settings.PLATFORM_NAME
            }
            template = get_template(txt_template)
            plain_content = template.render(context)
            template = get_template(html_template)
            html_content = template.render(context)

            email_msg = EmailMultiAlternatives(
                subject, plain_content, from_address, to=to_addresses
            )
            email_msg.attach_alternative(html_content, 'text/html')
            email_msg.send()

    except Exception:  # pylint: disable=broad-except
        error_message = 'Failed to send email notifications for preview available of course-run {run_id}'.format(
            run_id=course_run.id
        )
        logger.exception(error_message)
        raise Exception(error_message)


def send_course_run_published_email(course_run):
    """ Send email when course run is published by publisher.

        Arguments:
            course_run (Object): CourseRun object
    """
    txt_template = 'publisher/email/course_run/published.txt'
    html_template = 'publisher/email/course_run/published.html'
    course_team_user = course_run.course.course_team_admin

    try:
        if is_email_notification_enabled(course_team_user):
            course_key = CourseKey.from_string(course_run.lms_course_id)
            subject = _('Publication complete: {course_name} {run_number}').format(     # pylint: disable=no-member
                course_name=course_run.course.title,
                run_number=course_key.run
            )
            to_addresses = [course_team_user.email]
            from_address = settings.PUBLISHER_FROM_EMAIL
            project_coordinator = course_run.course.project_coordinator
            page_path = reverse('publisher:publisher_course_run_detail', kwargs={'pk': course_run.id})
            course_page_path = reverse('publisher:publisher_course_detail', kwargs={'pk': course_run.course.id})
            context = {
                'sender_role': PublisherUserRole.Publisher,
                'course_name': course_run.course.title,
                'preview_url': course_run.preview_url,
                'course_run_number': course_key.run,
                'recipient_name': course_team_user.get_full_name() or course_team_user.username,
                'contact_us_email': project_coordinator.email if project_coordinator else '',
                'page_url': 'https://{host}{path}'.format(
                    host=Site.objects.get_current().domain.strip('/'), path=page_path
                ),
                'course_page_url': 'https://{host}{path}'.format(
                    host=Site.objects.get_current().domain.strip('/'), path=course_page_path
                ),
                'platform_name': settings.PLATFORM_NAME,
            }
            template = get_template(txt_template)
            plain_content = template.render(context)
            template = get_template(html_template)
            html_content = template.render(context)

            email_msg = EmailMultiAlternatives(
                subject, plain_content, from_address, to=to_addresses
            )
            email_msg.attach_alternative(html_content, 'text/html')
            email_msg.send()

    except Exception:  # pylint: disable=broad-except
        error_message = 'Failed to send email notifications for course published of course-run [{run_id}]'.format(
            run_id=course_run.id
        )
        logger.exception(error_message)
        raise Exception(error_message)


def send_change_role_assignment_email(course_role, former_user):
    """ Send email for role assignment changed.

        Arguments:
            course_role (Object): CourseUserRole object
            former_user (Object): User object
    """
    txt_template = 'publisher/email/role_assignment_changed.txt'
    html_template = 'publisher/email/role_assignment_changed.html'

    try:
        role_name = course_role.get_role_display()
        subject = _('{role_name} changed for {course_title}').format(  # pylint: disable=no-member
            role_name=role_name.lower(),
            course_title=course_role.course.title
        )
        to_addresses = course_role.course.get_course_users_emails()
        to_addresses.append(former_user.email)
        if course_role.course.course_team_admin:
            to_addresses.remove(course_role.course.course_team_admin.email)

        from_address = settings.PUBLISHER_FROM_EMAIL
        project_coordinator = course_role.course.project_coordinator
        page_path = reverse('publisher:publisher_course_detail', kwargs={'pk': course_role.course.id})
        context = {
            'course_title': course_role.course.title,
            'role_name': role_name.lower(),
            'former_user_name': former_user.get_full_name() or former_user.username,
            'current_user_name': course_role.user.get_full_name() or course_role.user.username,
            'contact_us_email': project_coordinator.email if project_coordinator else '',
            'course_url': 'https://{host}{path}'.format(
                host=Site.objects.get_current().domain.strip('/'), path=page_path
            ),
            'platform_name': settings.PLATFORM_NAME,
        }
        template = get_template(txt_template)
        plain_content = template.render(context)
        template = get_template(html_template)
        html_content = template.render(context)

        email_msg = EmailMultiAlternatives(
            subject, plain_content, from_address, to=to_addresses
        )
        email_msg.attach_alternative(html_content, 'text/html')
        email_msg.send()

    except Exception:  # pylint: disable=broad-except
        error_message = 'Failed to send email notifications for change role assignment of role: [{role_id}]'.format(
            role_id=course_role.id
        )
        logger.exception(error_message)
        raise Exception(error_message)
