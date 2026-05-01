import os, django, re
os.environ.setdefault('DJANGO_SETTINGS_MODULE','rental_app.settings')
django.setup()
from django.template.loader import get_template
t = get_template('index.html')
html = t.render({'hide_navbar': True, 'hide_sidebar': True})
print('NAV_PRESENT', bool(re.search(r'<nav\s', html)))
print('DIV_NAV_PRESENT', '<div class="navbar"' in html)
print('FOUND_SNIPPET:', html[html.find('<nav class=')-120:html.find('<nav class=')+240] if '<nav class=' in html else 'no nav found')
