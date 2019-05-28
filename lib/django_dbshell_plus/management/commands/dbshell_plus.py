import errno
import subprocess
import sys

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
                # attempt to use mycli/pgcli
                getattr(self, cmd)(connection)
                return
            except OSError, e:
                if self._is_virtualenv:
                    try:
                        # retry without explicitly without virtualenv
                        getattr(self, cmd)(connection, ignore_virtualenv=True)
                        return
                    except OSError, e:
                        if e.errno != errno.ENOENT:
                            self.stderr.write("Could not start %s: %s" % (cmd, str(e)))
                else:
                    if e.errno != errno.ENOENT:
                        self.stderr.write("Could not start %s: %s" % (cmd, str(e)))

        # default to system mysql/psql
        super(Command, self).handle(**options)

    @property
    def _is_virtualenv(self):
        # sys.real_prefix is only set if inside virtualenv
        return hasattr(sys, 'real_prefix')

    @property
    def _python_path(self):
        path = '{}/bin/'.format(sys.prefix) if self._is_virtualenv else ''
        return path

    def _get_cli_command(self, cli, ignore_virtualenv=False):
        cli_command = '{}{}'.format(
            '' if ignore_virtualenv else self._python_path,
            cli, # 'pgcli' or 'mycli'
        )
        return cli_command

    def pgcli(self, connection, ignore_virtualenv=False):
        # argument code copied from Django
        settings_dict = connection.settings_dict
        args = [self._get_cli_command('pgcli', ignore_virtualenv=ignore_virtualenv)]
        if settings_dict['USER']:
            args += ["-U", settings_dict['USER']]
        if settings_dict['HOST']:
            args.extend(["-h", settings_dict['HOST']])
        if settings_dict['PORT']:
            args.extend(["-p", str(settings_dict['PORT'])])
        args += [settings_dict['NAME']]

        subprocess.call(args)

    def mycli(self, connection, ignore_virtualenv=False):
        # argument code copied from Django
        settings_dict = connection.settings_dict
        args = [self._get_cli_command('mycli', ignore_virtualenv=ignore_virtualenv)]
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
