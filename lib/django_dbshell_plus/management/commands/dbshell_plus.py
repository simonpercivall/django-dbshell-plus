import errno
import subprocess

from django.db import connections
from django.core.management.commands import dbshell


class Command(dbshell.Command):

    def handle(self, **options):
        connection = connections[options.get('database')]

        dbclis = {
            'postgresql': 'pgcli',
            'mysql': 'mycli'
        }

        cmd = dbclis.get(connection.vendor)
        if cmd:
            try:
                getattr(self, cmd)(connection)
                return
            except OSError, e:
                if e.errno != errno.ENOENT:
                    self.stderr.write("Could not start %s: %s" % (cmd, str(e)))

        super(Command, self).handle(**options)

    def pgcli(self, connection):
        # argument code copied from Django
        settings_dict = connection.settings_dict
        args = ['pgcli']
        if settings_dict['USER']:
            args += ["-U", settings_dict['USER']]
        if settings_dict['HOST']:
            args.extend(["-h", settings_dict['HOST']])
        if settings_dict['PORT']:
            args.extend(["-p", str(settings_dict['PORT'])])
        args += [settings_dict['NAME']]

        subprocess.call(args)

    def mycli(self, connection):
        # argument code copied from Django
        settings_dict = connection.settings_dict
        args = ['mycli']
        db = settings_dict['OPTIONS'].get('db', settings_dict['NAME'])
        user = settings_dict['OPTIONS'].get('user', settings_dict['USER'])
        passwd = settings_dict['OPTIONS'].get('passwd', settings_dict['PASSWORD'])
        host = settings_dict['OPTIONS'].get('host', settings_dict['HOST'])
        port = settings_dict['OPTIONS'].get('port', settings_dict['PORT'])

        if user:
            args += ["--user=%s" % user]
        if passwd:
            args += ["--pass=%s" % passwd]
        if host:
            if '/' in host:
                args += ["--socket=%s" % host]
            else:
                args += ["--host=%s" % host]
        if port:
            args += ["--port=%s" % port]
        if db:
            args += [db]

        subprocess.call(args)
