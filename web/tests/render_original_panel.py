"""Read-only template rendering for visual comparison; never logs into the reference.

Output is written under the current checkout's ignored build directory. All values
are explicitly fictitious. No reference database, accounts, files or services change.
"""
import os
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.template import Engine, Context
from django.test import RequestFactory, override_settings
from django.utils import timezone

reference = Path(os.environ.get('DISPENSALUD_ORIGINAL', 'D:/dispensalud-web-original'))
request = RequestFactory().get('/panel/')
request.session = {'api_token': 'ficticio-no-authentication'}
selected = {'id':'fixture-person', 'displayName':'FICTICIO · Paciente diseño'}
engine = Engine(dirs=[reference / 'web/portal/templates'], libraries={'static':'django.templatetags.static'})
context = {
    'request':request, 'account':{'role':'CAREGIVER'}, 'selected':selected,
    'people':[selected], 'now':timezone.now(), 'section':'hoy', 'adult_mode':False,
    'medications':[{'name':'FICTICIO · Tratamiento diseño'}], 'active_schedules':1,
    'open_requests':[], 'plan':{'date':date.today().isoformat(), 'doses':[]},
    'messages':[], 'upcoming':None, 'preview':False, 'csrf_token':'NOTPROVIDED',
}
with override_settings(ROOT_URLCONF='config.legacy_urls'):
    html = engine.get_template('portal/caregiver.html').render(Context(context))
html = html.replace('href="/static/', 'href="http://localhost:8001/static/').replace('src="/static/', 'src="http://localhost:8001/static/')
output = Path(__file__).resolve().parents[1] / 'build/original-panel.html'
output.parent.mkdir(exist_ok=True)
output.write_text(html, encoding='utf-8')
print('Read-only original template rendered with fictitious values:', output)
