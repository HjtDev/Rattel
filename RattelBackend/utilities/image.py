import io
import random
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image


def generate_random_image(width: int, height: int, upload_to: str) -> str:
    """
    Generate a random grayscale placeholder image and save it to the media folder.

    Args:
        width:     Image width in pixels.
        height:    Image height in pixels.
        upload_to: Relative path within MEDIA_ROOT to save the image
                   (e.g. 'landing_contents/image').

    Returns:
        The saved file path relative to MEDIA_ROOT, ready to be assigned
        directly to a Django ImageField or FileField.
    """
    shade = random.randint(0, 255)
    img = Image.new('RGB', (width, height), color=(shade, shade, shade))

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)

    filename = f'{upload_to}/default_{width}x{height}.jpg'
    saved_path = default_storage.save(filename, ContentFile(buffer.read()))

    return saved_path