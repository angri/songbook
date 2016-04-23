import re
import json

from django.contrib.messages.api import get_messages
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.urlresolvers import reverse
from django.utils import translation
from django.utils import timezone
import jinja2
import markdown
import babel.dates


def markdown_safe(text):
    md = markdown.Markdown(output_format='html5')
    return jinja2.Markup(md.convert(jinja2.escape(text)))


def url(name, *args, **kwargs):
    return reverse(name, args=args, kwargs=kwargs)


def csrf(token):
    return jinja2.Markup(
        '<input type="hidden" name="csrfmiddlewaretoken" value="%s">' %
        jinja2.escape(token)
    )


_is_youtube_link_re = re.compile(
    r"^https?://(youtu\.be|(www\.)?youtube\.com)/.+"
)
_get_youtube_iframe_url_re = re.compile(
    r".*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]*).*"
)

_get_yamusic_embed_link_re = re.compile(
    r"https://music\.yandex\.ru/album/(?P<album>\d+)/track/(?P<track>\d+)"
)


def is_youtube_link(link):
    """
    >>> iyl = is_youtube_link
    >>> iyl("http://www.youtube.com/v/0z")
    True
    >>> iyl("https://www.youtube.com/v/0z")
    True
    >>> iyl("http://youtu.be/0z")
    True
    >>> iyl("http://youtu.bez/0z")
    False
    """
    return _is_youtube_link_re.match(link) is not None


def get_youtube_embed_link(link):
    """
    >>> gyel = get_youtube_embed_link
    >>> gyel("http://www.youtube.com/" \
             "watch?v=0zM3nApSvMg&feature=feedrec_grec_index")
    'https://www.youtube.com/embed/0zM3nApSvMg'
    >>> gyel("http://www.youtube.com/" \
             "user/IngridMichaelsonVEVO#p/a/u/1/QdK8U-VIH_o")
    'https://www.youtube.com/embed/QdK8U-VIH_o'
    >>> gyel("http://www.youtube.com/" \
             "v/0zM3nApSvMg?fs=1&amp;hl=en_US&amp;rel=0")
    'https://www.youtube.com/embed/0zM3nApSvMg'
    >>> gyel("http://www.youtube.com/watch?v=0zM3nApSvMg#t=0m10s")
    'https://www.youtube.com/embed/0zM3nApSvMg'
    >>> gyel("http://www.youtube.com/embed/0zM3nApSvMg?rel=0")
    'https://www.youtube.com/embed/0zM3nApSvMg'
    >>> gyel("http://www.youtube.com/watch?v=0zM3nApSvMg")
    'https://www.youtube.com/embed/0zM3nApSvMg'
    >>> gyel("http://youtu.be/0zM3nApSvMg")
    'https://www.youtube.com/embed/0zM3nApSvMg'
    """
    m = _get_youtube_iframe_url_re.match(link)
    if m is None:
        return None
    [video_id] = m.groups()
    return "https://www.youtube.com/embed/" + video_id


def is_yamusic_link(link):
    return link.startswith('https://music.yandex.ru/')


def get_yamusic_embed_link(link):
    """
    >>> gyel = get_yamusic_embed_link
    >>> gyel('https://music.yandex.ru/album/35627/track/354089')
    'https://music.yandex.ru/iframe/#track/354089/35627'
    """
    m = _get_yamusic_embed_link_re.match(link)
    if m is None:
        return None
    return 'https://music.yandex.ru/iframe/#track/%(track)s/%(album)s' % \
           m.groupdict()


def format_datedelta(date):
    td = date - timezone.now().date()
    locale = translation.trans_real.get_language()
    return babel.dates.format_timedelta(td, add_direction=True,
                                        locale=locale)


def format_timedelta(dt):
    td = dt - timezone.now()
    locale = translation.trans_real.get_language()
    return babel.dates.format_timedelta(td, add_direction=True,
                                        locale=locale)


def format_date(date, format='medium'):
    locale = translation.trans_real.get_language()
    return babel.dates.format_date(date, format=format, locale=locale)


def format_datetime(dt, format='medium'):
    tz = timezone.get_current_timezone()
    locale = translation.trans_real.get_language()
    return babel.dates.format_datetime(dt, format=format, locale=locale,
                                       tzinfo=tz)


def decode_json(data):
    return json.loads(data)


def environment(**options):
    extensions = ['jinja2.ext.i18n',
                  'jinja2.ext.with_']
    env = jinja2.Environment(**options, extensions=extensions)
    env.install_gettext_translations(translation, newstyle=True)
    env.globals.update({
        'messages': get_messages,
        'static': staticfiles_storage.url,
        'url': url,
        'csrf': csrf,
    })
    env.filters.update({
        'format_datedelta': format_datedelta,
        'format_timedelta': format_timedelta,
        'format_datetime': format_datetime,
        'format_date': format_date,
        'decode_json': decode_json,
        'markdown_safe': markdown_safe,
        'is_youtube_link': is_youtube_link,
        'get_youtube_embed_link': get_youtube_embed_link,
        'is_yamusic_link': is_yamusic_link,
        'get_yamusic_embed_link': get_yamusic_embed_link,
    })
    return env
