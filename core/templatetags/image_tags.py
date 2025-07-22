from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
import os

register = template.Library()


@register.simple_tag
def optimized_image(src, alt="", css_class="", lazy=True, aspect_ratio=None, sizes="100vw"):
    """
    Render an optimized image with lazy loading and WebP support
    
    Usage:
    {% optimized_image "path/to/image.jpg" "Alt text" "css-class" lazy=True aspect_ratio="16-9" %}
    """
    if not src:
        return ""
    
    # Generate WebP version path
    webp_src = generate_webp_path(src)
    
    # Build CSS classes
    classes = ["img-optimized"]
    if lazy:
        classes.append("img-lazy")
    if css_class:
        classes.append(css_class)
    
    # Build container classes
    container_classes = ["img-container"]
    if aspect_ratio:
        container_classes.append(f"img-container-{aspect_ratio}")
    
    # Build image attributes
    img_attrs = {
        'alt': alt,
        'class': ' '.join(classes),
        'loading': 'lazy' if lazy else 'eager',
    }
    
    if lazy:
        img_attrs['data-src'] = src
        if webp_src:
            img_attrs['data-webp'] = webp_src
        img_attrs['src'] = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PC9zdmc+'
    else:
        img_attrs['src'] = src
    
    # Build HTML
    img_html = format_html('<img {}>', ' '.join(f'{k}="{v}"' for k, v in img_attrs.items()))
    
    if aspect_ratio:
        return format_html(
            '<div class="{}">{}</div>',
            ' '.join(container_classes),
            img_html
        )
    
    return img_html


@register.simple_tag
def responsive_image(src, alt="", css_class="", lazy=True, breakpoints=None):
    """
    Render a responsive image with different sources for different screen sizes
    
    Usage:
    {% responsive_image "image.jpg" "Alt text" breakpoints="768:image-md.jpg,1200:image-lg.jpg" %}
    """
    if not src:
        return ""
    
    # Parse breakpoints
    sources = []
    if breakpoints:
        for bp in breakpoints.split(','):
            if ':' in bp:
                width, bp_src = bp.split(':', 1)
                sources.append((int(width), bp_src))
    
    # Sort by width (largest first)
    sources.sort(key=lambda x: x[0], reverse=True)
    
    # Build picture element
    picture_html = ['<picture>']
    
    # Add source elements for each breakpoint
    for width, bp_src in sources:
        webp_src = generate_webp_path(bp_src)
        
        if webp_src:
            picture_html.append(
                f'<source media="(min-width: {width}px)" srcset="{webp_src}" type="image/webp">'
            )
        picture_html.append(
            f'<source media="(min-width: {width}px)" srcset="{bp_src}">'
        )
    
    # Add WebP fallback for main image
    webp_src = generate_webp_path(src)
    if webp_src:
        picture_html.append(f'<source srcset="{webp_src}" type="image/webp">')
    
    # Add main img element
    classes = ["img-optimized"]
    if lazy:
        classes.append("img-lazy")
    if css_class:
        classes.append(css_class)
    
    img_attrs = {
        'src': src,
        'alt': alt,
        'class': ' '.join(classes),
        'loading': 'lazy' if lazy else 'eager',
    }
    
    picture_html.append(format_html('<img {}>', ' '.join(f'{k}="{v}"' for k, v in img_attrs.items())))
    picture_html.append('</picture>')
    
    return mark_safe(''.join(picture_html))


@register.simple_tag
def image_placeholder(width=300, height=200, text="", bg_color="#ddd", text_color="#999"):
    """
    Generate a placeholder image
    
    Usage:
    {% image_placeholder 300 200 "Loading..." %}
    """
    svg = f'''
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="{bg_color}"/>
        {f'<text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="{text_color}" font-family="Arial, sans-serif" font-size="14">{text}</text>' if text else ''}
    </svg>
    '''
    
    encoded_svg = svg.replace('\n', '').replace('  ', ' ')
    data_url = f"data:image/svg+xml;charset=utf-8,{encoded_svg}"
    
    return format_html(
        '<img src="{}" width="{}" height="{}" alt="Placeholder" class="img-placeholder">',
        data_url, width, height
    )


@register.filter
def webp_url(image_url):
    """
    Convert image URL to WebP version
    
    Usage:
    {{ image.url|webp_url }}
    """
    return generate_webp_path(image_url) or image_url


@register.inclusion_tag('includes/optimized_image.html')
def include_optimized_image(src, alt="", css_class="", lazy=True, aspect_ratio=None, overlay=False):
    """
    Include an optimized image using a template
    
    Usage:
    {% include_optimized_image "image.jpg" "Alt text" "css-class" lazy=True aspect_ratio="16-9" overlay=True %}
    """
    return {
        'src': src,
        'webp_src': generate_webp_path(src),
        'alt': alt,
        'css_class': css_class,
        'lazy': lazy,
        'aspect_ratio': aspect_ratio,
        'overlay': overlay,
    }


def generate_webp_path(image_path):
    """
    Generate WebP version path for an image
    """
    if not image_path:
        return None
    
    # Remove query parameters
    base_path = image_path.split('?')[0]
    
    # Get file extension
    name, ext = os.path.splitext(base_path)
    
    # Skip if already WebP
    if ext.lower() == '.webp':
        return None
    
    # Generate WebP path
    webp_path = f"{name}.webp"
    
    return webp_path


@register.simple_tag
def preload_image(src, as_type="image"):
    """
    Generate preload link for critical images
    
    Usage:
    {% preload_image "hero-image.jpg" %}
    """
    if not src:
        return ""
    
    return format_html(
        '<link rel="preload" as="{}" href="{}">',
        as_type, src
    )


@register.simple_tag
def image_srcset(base_src, widths="320,640,960,1280"):
    """
    Generate srcset attribute for responsive images
    
    Usage:
    {% image_srcset "image.jpg" "320,640,960,1280" %}
    """
    if not base_src:
        return ""
    
    name, ext = os.path.splitext(base_src)
    srcset_items = []
    
    for width in widths.split(','):
        width = width.strip()
        responsive_src = f"{name}-{width}w{ext}"
        srcset_items.append(f"{responsive_src} {width}w")
    
    return ', '.join(srcset_items)


@register.filter
def add_image_params(url, params):
    """
    Add parameters to image URL for dynamic resizing
    
    Usage:
    {{ image.url|add_image_params:"w=300&h=200&q=85" }}
    """
    if not url or not params:
        return url
    
    separator = '&' if '?' in url else '?'
    return f"{url}{separator}{params}"
