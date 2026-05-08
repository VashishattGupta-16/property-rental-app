from django import template

register = template.Library()


def _as_url(value):
    if not value:
        return ""
    try:
        return value.url
    except (AttributeError, ValueError):
        return str(value)


@register.filter
def secure_media_url(value):
    url = _as_url(value)
    if url.startswith("http://"):
        return "https://" + url.removeprefix("http://")
    return url


@register.filter
def optimized_cloudinary_url(value, transformations="f_auto,q_auto,c_limit,w_1200"):
    url = secure_media_url(value)
    if "/image/upload/" not in url or transformations in url:
        return url
    return url.replace("/image/upload/", f"/image/upload/{transformations}/", 1)
