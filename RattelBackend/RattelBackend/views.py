from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin


class TinyMCEImageUploadView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def post(self, request):
        image = request.FILES.get('file')
        if not image:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message='No file provided.'
            )

        is_valid, errors = self.validate_uploaded_file(
            image,
            max_size=5 * 1024 * 1024,
            allowed_mime_types=('image/jpeg', 'image/png', 'image/webp'),
            allowed_extensions=('jpg', 'jpeg', 'png', 'webp'),
        )
        if not is_valid:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-2,
                message=errors
            )

        saved_path = default_storage.save(f'editor/{image.name}', image)
        file_url = request.build_absolute_uri(default_storage.url(saved_path))

        # TinyMCE expects this exact payload shape.
        return self.build_response(status.HTTP_200_OK, location=file_url)
