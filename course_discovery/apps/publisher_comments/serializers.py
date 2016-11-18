"""Publisher Serializers"""
from rest_framework import serializers

from course_discovery.apps.publisher_comments.models import Comments


class UpdateCommentSerializer(serializers.ModelSerializer):
    """Serializer for the `Comment` model to update existing `comment`. """

    class Meta:
        model = Comments
        fields = ('comment', 'id', )
