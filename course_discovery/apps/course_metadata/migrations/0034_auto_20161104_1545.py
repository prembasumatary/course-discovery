# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0033_courserun_mobile_available'),
    ]

    operations = [
        migrations.CreateModel(
            name='CanonicalCourseRunCourse',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('course', models.ForeignKey(to='course_metadata.Course', unique=True, related_name='canonical_courses')),
                ('course_run', models.ForeignKey(to='course_metadata.CourseRun', unique=True, related_name='canonical_course_runs')),
            ],
            options={
                'abstract': False,
                'ordering': ('-modified', '-created'),
                'get_latest_by': 'modified',
            },
        ),
        migrations.AddField(
            model_name='course',
            name='_canonical_course_runs',
            field=models.ManyToManyField(related_name='canonical_courses', through='course_metadata.CanonicalCourseRunCourse', to='course_metadata.CourseRun'),
        ),
        migrations.AddField(
            model_name='courserun',
            name='_canonical_courses',
            field=models.ManyToManyField(related_name='canonical_course_runs', through='course_metadata.CanonicalCourseRunCourse', to='course_metadata.Course'),
        ),
    ]
