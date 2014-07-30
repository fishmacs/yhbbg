#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    ### can not find bookbag_admin.settings if insert(0,...)
    sys.path.insert(1, os.path.abspath('..'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookbag_admin.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
