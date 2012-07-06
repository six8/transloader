from datetime import datetime, timedelta
import hashlib
import hmac
import requests

try:
    import simplejson as json
except ImportError:
    import json

def _timestr(dt):
    """
    Convert datetime to Transloadit timestring
    """
    if dt is None:
        return dt
    elif hasattr(dt, 'strftime'):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return str(dt)


def _parse_response(response):
    if response.json and response.json.get('error'):
        raise TransloadItError(response.json.get('message'), response.json.get('error'), response.status_code)

    if response.status_code < 200 or response.status_code >= 400:
        raise TransloadItError(response.text, None, response.status_code)
    return response

class TransloadItError(Exception):
    def __init__(self, message, code, status):
        super(TransloadItError, self).__init__(message)
        self.message = message
        self.code = code
        self.status = status

    def __str__(self):
        return '%s (%s): %s' % (self.code, self.status, self.message)

class TransloadIt(object):
    def __init__(self, key, secret):
        """
        :param key: TransloadIt API key
        :param secret: TransloadIt API secret
        """
        self.key = key
        self.secret = secret

    def sign(self, params):
        """
        Sign a request
        """
        return hmac.new(self.secret, params, hashlib.sha1).hexdigest()

    def _auth(self):
        return dict(
            key = self.key,
            expires = (datetime.utcnow() + timedelta(days=1)).strftime('%Y/%m/%d %H:%M:%S')
        )

    def _params(self, **kwargs):
        params = dict(auth=self._auth())
        for k,v in kwargs.items():
            if v is None:
                continue
            elif isinstance(v, datetime):
                v = _timestr(v)

            params[k] = v
        return params

    def replay_assembly(self, assembly_id, notify_url=None, reparse_template=False):
        """
        Replays an assembly.

        :param notify_url: a new notify_url if you do not want to use the one of the assembly that should be replayed.
        :param reparse_template: True if you want to reparse the template that was used in your assembly
        """
        params = self._params(
            notify_url = notify_url,
            reparse_template = 1 if reparse_template else 0,
        )

        params = json.dumps(params)

        response = _parse_response(requests.post(
            'http://api2.transloadit.com/assemblies/%s/replay' % assembly_id,
            data=dict(params=params, signature=self.sign(params)),
        ))

        return Assembly(response.json['assembly_url'])

    def replay_assembly_notification(self, assembly_id):
        """
        Replays an assembly notification.
        """
        params = self._params()

        params = json.dumps(params)

        response = _parse_response(requests.post(
            'http://api2.transloadit.com/assemblies/%s/replay_notification' % assembly_id,
            data=dict(params=params, signature=self.sign(params)),
        ))

        return Assembly(response.json['assembly_url'])

    def create_assembly(self, template_id, file=None, steps=None, fields=None, notify_url=None, redirect_url=None):
        """
        :param template_id: transloadit.com template id
        :param file: File like object to upload as source media
        :param steps: dict - Steps to recursively merge into your template
        :param fields: dict - Additional variables that will be available as `${fields.<key>}` in your templates

        @see https://transloadit.com/docs/passing-fields-and-variables-into-templates
        """

        params = self._params(
            template_id = template_id,
            steps = steps,
            fields = fields,
            notify_url = notify_url,
            redirect_url = redirect_url
        )

        params = json.dumps(params)
        response = _parse_response(requests.post(
            'http://api2.transloadit.com/assemblies',
            data=dict(params=params, signature=self.sign(params)),
            files=[file] if file else None
        ))

        return Assembly(response.json['assembly_url'])

    def assemblies(self, page=1, pagesize=100, type='all', fromdate=None, todate=None, keywords=None):
        """
        Retrieves a list of assemblies for your accounts. Returns an iterator that automatically
        handles pagination.

        page	Specify which page (in your pagination) you are on. The default value is 1.
        pagesize	 Specify how many assemblies you want to receive per api request. This is useful for pagination. The maximum value is 850.
        type	 Which types of assemblies do you want to retrieve. Can be "uploading", "executing", "canceled", "completed" or "request_aborted". Default value is all.
        fromdate	 Retrieve assemblies that were created after this datetime. Format is Y-m-d H:i:s.
        todate	 Retrieve assemblies that were created before this datetime. Format is Y-m-d H:i:s.
        keywords	 Search for a string in the assembly json. Matches assembly id's, redirect_url's, notify_url's, error messages and used files.
        """

        while True:
            params = self._params(
                page = page,
                pagesize = pagesize,
                type = type,
                fromdate = _timestr(fromdate),
                todate = _timestr(todate),
                keywords=keywords,
            )

            params = json.dumps(params)
            response = requests.get(
                'http://api2.transloadit.com/assemblies',
                params=dict(params=params, signature=self.sign(params)),
            )

            response = _parse_response(response)

            data = response.json

            count = data['count']
            items = data['items']
            num_items = len(data['items'])
            pos = page * pagesize

            if not num_items:
                break

            for item in items:
                yield Assembly(
                    url='http://jsondb.transloadit.com.s3.amazonaws.com/assemblies/%s.json' % item['id'],
                    **item
                )

            if pos < count:
                page += 1
            else:
                break

class Assembly(object):
    def __init__(self, url, **kwargs):
        self.url = url
        self._info = kwargs

    def refresh(self):
        """
        Re-fetch status from server
        """
        self._info = None
        return self.info

    @property
    def info(self):
        if not self._info:
            response = requests.get(self.url)
            response = _parse_response(response)
            self._info = response.json
        return self._info

    @property
    def completed(self):
        """
        True if the assembly completed successfully
        """
        return self.info['ok'] == 'ASSEMBLY_COMPLETED'

    @property
    def canceled(self):
        """
        True if the assembly was cancelled
        """
        return self.info['ok'] == 'ASSEMBLY_CANCELED'

    def cancel(self):
        """
        Cancels an assembly / upload that is still in progress.
        """
        return requests.delete(self.url)

    def __getattr__(self, name):
        return self.info.get(name, None)

    def __repr__(self):
        return u'<%s %s %s>' % (
            self.__class__.__name__,
            self.url,
            json.dumps(dict(
                ((k, unicode(v)) for k, v in self._info.items())
            )) if self._info else ''
        )

