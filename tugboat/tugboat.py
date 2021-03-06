#!/usr/bin/python
"""
A Python Tk application to edit Jamf computer records.
"""
# -*- coding: utf-8 -*-

# Copyright (c) 2018 University of Utah Student Computing Labs. ################
# All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and
# its documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appears in all copies and
# that both that copyright notice and this permission notice appear
# in supporting documentation, and that the name of The University
# of Utah not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission. This software is supplied as is without expressed or
# implied warranties of any kind.
################################################################################

# tugboat.py #################################################
#
# A Python Tk application to edit Jamf computer records.
#
#
#    1.5.0  2017.02.15      Initial public release. tjm
#
#    1.5.2  2017.02.15      Logging with management_tools, login and search
#                           much improved, top user improved. Other tweaks. tjm
#
#    1.5.3  2018.01.xx      Added LDAP login logic. tjm
#
#    1.5.4  2018.01.15      Host preference file. tjm
#                           Light code cleanup
#
#    1.7.0  2018.01.25      Full/Auditing user login support. tjm
#                           Increased, fine-grained logging.
#
#    1.7.1  2018.01.28      UI limited in audit mode. tjm
#                           Bug in login code corrected.
#
################################################################################

# notes: #######################################################################
#
#     py2app (macOS):
#     rm -rdf build dist ; /usr/bin/python setup.py py2app -s
#
#     pyinstaller (Windows):
#     pyinstaller --onefile -i tugboat_icon.ico tugboat.py
#
################################################################################

# TTD: #########################################################################
#
#     Unify all jss calls in single generic method, something like:
#           ('call_jss(logger, api_call)')
#
#     Add correct windows logging.
#
#
################################################################################

from __future__ import print_function
import base64
import ConfigParser
import inspect
import json
import os
import platform
import re
import socket
import subprocess
import sys
import tkFont
import tkMessageBox
import tkSimpleDialog
import ttk
import urllib
import urllib2
import webbrowser
import xml.etree.cElementTree as ET
from Tkinter import *

#
# Need to implement correct windows-appropriate logging.
if platform.system() == 'Darwin':
    import pexpect
    import pwd
    try:
        from management_tools import loggers
    except:
        import logging
else:
    try:
        from management_tools import loggers
    except:
        import logging


class Computer(object):
    """
    Store GUI and data structures describing jamf computer records
    """
    def __init__(self, root, logger, jamf_hostname, jamf_username, jamf_password, access_level):
        """
        initialize variables and data structures
        """
        self.root = root
        self.logger = logger
        self.jamf_hostname = jamf_hostname
        self.jamf_password = jamf_password
        self.jamf_username = jamf_username
        self.access_level = access_level
        self.local_jamf_id = None

        self.hostname = ""
        self.divisions = []
        self.buildings = []
        self.platform = None
        self.will_offboard = False
        self.jamf_management = ""

        self.username_string = StringVar()
        self.fullname_string = StringVar()
        self.department_string = StringVar()
        self.position_string = StringVar()
        self.email_string = StringVar()
        self.phone_string = StringVar()
        self.building_string = StringVar()
        self.room_string = StringVar()
        self.assettag_string = StringVar()
        self.barcode_string = StringVar()
        self.status_string = StringVar()
        self.id_string = StringVar()
        self.search_string = StringVar()
        self.computer_name_string = StringVar()

        self.username_string.set("")
        self.fullname_string.set("")
        self.position_string.set("")
        self.email_string.set("")
        self.phone_string.set("")
        self.room_string.set("")
        self.assettag_string.set("")
        self.status_string.set("Logged in to " + self.jamf_hostname + " with " + access_level + " privileges.")
        self.computer_name_string.set("")

        self.status_warning = ttk.Style()
        self.status_warning.configure('Warning.TLabel', foreground='red')

        self.status_normal = ttk.Style()
        self.status_normal.configure('Normal.TLabel', foreground='black')

        self.highlight_button = ttk.Style()
        self.highlight_button.configure('Highlight.TButton', foreground='green')

        self.dim_text = ttk.Style()
        self.dim_text.configure('Dim.TLabel', foreground='gray50')

        self.black_text = ttk.Style()
        self.black_text.configure('Black.TLabel', foreground='black')

        self.status_subtle = ttk.Style()
        self.status_subtle.configure('Subtle.TLabel', foreground='maroon')

        self.hostname = (socket.gethostname()).split(".")[0]
        self.divisions = self.populate_menu('departments')
        self.buildings = self.populate_menu('buildings')

        self.build_ui()

    def build_ui(self):
        """
        describe UI, fields, buttons, etc
        """

        #
        # This is an encoded gif of the title image
        self.logo_image = '''\
        R0lGODlhWAJRAPcAAAEAAAQECgYJCgwMDQgHCBMODQ4QDhERDg0OEQUHFREOEw4REgoTGhITFBQV
        GhUZGxsbHBkXGCcXFR0iHiwkHRwdIxYZJhAVLyIcIxwjJRcpNiUlJSQlKyUqLCwrLCknJzQqKCgr
        NjMtNSwyOTMzNTM0Ozs7PDk3ODYyK1ExFWo3Ekc3KUQ7OlY0LF8rKD9DPHdIGnBJGUpEO1ZJOVdJ
        LHZLJXBRMHdhNxknQicqRS01RTM1Qjs8Qzg6Ry86VRkvWEQ9REk+TGYzQD1DSDlFVTlTY0NCQ0RD
        S0xLTEtHR1NLSVhSS0hJVlJNU1ROWExTWFVSVFtUVFlZWVdVWkhTSGhXSGRaWXFQS2pkXXdoVEtV
        Z1dZZlFUa2VdZFVpbmxra2dlZ3Rpamdpdnx9fXd2d3FzcFJjWaE0MMQSMMcfO8chPMgjPtQyOPow
        OolXG4xRF5llHLBtGYhYJ5ZbJ4lVM5hmKYlmN5doN5NsMKhrJqd0KrZ4Kah4N7Z7NqxqN6VZKMh4
        L+BXLc46U8kqRPwxRoZnRpByT613TIt3bq51bpNYTtFGXtBFVch0TtRTaNJMY9lnevNvVXCNe1aP
        bj+EbriFObmEKsiIKNmZK8WIN8qUOdiYNtGPLOSZMNujOdymMOmmK/WqKPq1KueoN+2zOfW1NPS0
        O/u6PPm5N/OsN+CYG/7FOf/MMbKLTI+Idq+PbrCrcJSRYMeWRs6QT9mlRc+nVeeqRuyzRve5RO6y
        UcySbNOrbuyza+iTUv3FRfvOUPXKbv/rZHJ3hVZxkYF+hdtugN13iHiJh3ajmjOL5kiS342NjYeE
        hpycnJiVl5CQjrKUjJGpl7ColJadpqqqqqWnqLi4uLa2tbGwrpqjp9CYjuKKmeGFlOyXkc2wkPiq
        k8q3rPKxsOaap7XKne3Pj9TKtvLMruvZobu6w9m9xLjGyMXFxcfKydHR0d3d3dbV19LQz/DCyvnF
        w+zVzObk2vjt0Nrd5+np6eXm5fj16/T09Pzz9f////f3+uzu8d3h5yH5BAAAAAAALAAAAABYAlEA
        AAj+APkJHEiwoMGDCBMO1PdKRQoVgGzlojWLjgULCaj1E/KnHr93AufVoycNm8B+/PzhU8iypcuX
        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
        RXatYVEc4fS1X6tJYfhlV+YIAHbNrRlMDAJOjqk9GiNghmrgPyVGKH1QU5Uxgu3F4z9OGCb+U84K
        B3GIh0WIB24IBz/5h5hkmkK64W5jV6vJrdq9Xem01FJMY2sTJDiuGAImYAF4SSXoAlcogzGgQHcQ
        YkBGqHtYSiMmE1aW5dUR5LfkLH4Ih3iYB0EoZCr2E2eIrg0ARfmNuquJQdqtxWMWpEqu5GUeYWVr
        Zul04+RIjgJeANHUAiwQhmkYAzD44WuwhnZY5Vl+tdJohgf+AkQIDXJmZ5nxUzVQgzSQ53mm53q2
        53v+ToMYu2V+iAdjiId42AZjmIeEAQNlewAYZY7phObpnMFaTGOGliNPXuhqvgwCtgAk+AIywEp4
        cId8QOJ2BumQbud96AcP3IeTNmmSTmmVPumWbumU9sB82OC+EIdiiIdiWOSadQACQIEISNoz5lkj
        C1o5ouZqJlACnj1cxdwEiIANAAGG+AJmmAZwGGeRtuqrbmdBZZ2Z9hOKIQDuyduwbt9pRowCdtEG
        mAAeaIItKBhnqAZrYAd4eId1wAZsWAd88Id8wOq95uu+Zs1GmWhlkz3nkIA6I6tnwIZrQId2oIfo
        9evHhuzINlBsYIZniAxnaIZmqIZyaAd38FjJBu0V0BZt1tTq0Tbt00bt1Fbt1WbtBQ4IACH/C1hN
        UCBEYXRhWE1QPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtj
        OWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUg
        WE1QIENvcmUgNS42LWMxMzggNzkuMTU5ODI0LCAyMDE2LzA5LzE0LTAxOjA5OjAxICAgICAgICAi
        PgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1z
        eW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIi8+CiA8L3JkZjpSREY+
        CjwveDp4bXBtZXRhPgo8P3hwYWNrZXQgZW5kPSJyIj8+Af/+/fz7+vn49/b19PPy8fDv7u3s6+rp
        6Ofm5eTj4uHg397d3Nva2djX1tXU09LR0M/OzczLysnIx8bFxMPCwcC/vr28u7q5uLe2tbSzsrGw
        r66trKuqqainpqWko6KhoJ+enZybmpmYl5aVlJOSkZCPjo2Mi4qJiIeGhYSDgoGAf359fHt6eXh3
        dnV0c3JxcG9ubWxramloZ2ZlZGNiYWBfXl1cW1pZWFdWVVRTUlFQT05NTEtKSUhHRkVEQ0JBQD8+
        PTw7Ojk4NzY1NDMyMTAvLi0sKyopKCcmJSQjIiEgHx4dHBsaGRgXFhUUExIREA8ODQwLCgkIBwYF
        BAMCAQAAOw==
        '''

        self.root.title("Tugboat 1.7.1")

        self.mainframe = ttk.Frame(self.root)

        self.mainframe.grid(column=0, row=0, sticky=NSEW)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry('+0+0')

        #
        # position and display logo image
        self.logo_label = ttk.Label(self.mainframe)
        self.logo_photoimage = PhotoImage(data=self.logo_image)
        self.logo_label['image'] = self.logo_photoimage
        self.logo_label.grid(column=1, row=0, columnspan=4)

        ttk.Separator(self.mainframe, orient=HORIZONTAL).grid(row=30, columnspan=35, sticky=EW)

        #
        # these are the elements of the Navigation section of the UI
        ttk.Label(self.mainframe, text="Discovery Method:").grid(column=1, row=100, sticky=E)
        ttk.Button(self.mainframe, text="This Device", style='Highlight.TButton', command=self.query_jamf_me).grid(column=2, row=100, sticky=W)

        ttk.Button(self.mainframe, text="Search Jamf", command=self.search_string_jamf).grid(column=2, row=100, sticky=E)
        self.search_entry = ttk.Entry(self.mainframe, width=25, textvariable=self.search_string)
        self.search_entry.grid(column=3, row=100, columnspan=2, sticky=W)

        ttk.Label(self.mainframe, text="Jamf ID:                ").grid(column=4, row=100, sticky=E)
        self.id_entry = ttk.Entry(self.mainframe, width=6, textvariable=self.id_string)
        self.id_entry.grid(column=4, row=100, sticky=E)

        if platform.system() == 'Darwin':
            ttk.Label(self.mainframe, text="User Selection:").grid(column=1, row=150, sticky=E)
            if self.access_level == 'full':
                ttk.Button(self.mainframe, text="Top User (Admin Req.)", command=self.usage).grid(column=2, row=150, sticky=W)
            else:
                ttk.Button(self.mainframe, text="Top User (Admin Req.)", command=self.usage, state='disabled').grid(column=2, row=150, sticky=W)

        #
        # If you are considering adding UI elements to communicate with user database, place them here
        #

        ttk.Separator(self.mainframe, orient=HORIZONTAL).grid(row=300, columnspan=5, sticky=EW)

        #
        # these are the elements of the General section of the UI
        ttk.Label(self.mainframe, text="Computer Name:").grid(column=1, row=320, sticky=E)
        self.computername_entry = ttk.Entry(self.mainframe, textvariable=self.computer_name_string)
        self.computername_entry.grid(column=2, row=320, sticky=EW)

        ttk.Label(self.mainframe, text="Asset Tag:").grid(column=1, row=340, sticky=E)
        self.assettag_entry = ttk.Entry(self.mainframe, textvariable=self.assettag_string)
        self.assettag_entry.grid(column=2, row=340, sticky=EW)

        ttk.Label(self.mainframe, text="Bar Code:").grid(column=3, row=340, sticky=E)
        self.barcode_entry = ttk.Entry(self.mainframe, textvariable=self.barcode_string)
        self.barcode_entry.grid(column=4, row=340, sticky=EW)

        ttk.Separator(self.mainframe, orient=HORIZONTAL).grid(row=500, columnspan=5, sticky=EW)

        #
        # these are the elements of the User and Location section of the UI
        ttk.Label(self.mainframe, text="Username:").grid(column=1, row=550, sticky=E)
        self.endusername_entry = ttk.Entry(self.mainframe, textvariable=self.username_string)
        self.endusername_entry.grid(column=2, row=550, sticky=EW)

        ttk.Label(self.mainframe, text="Full Name:").grid(column=3, row=550, sticky=E)
        self.fullname_entry = ttk.Entry(self.mainframe, width=31, textvariable=self.fullname_string)
        self.fullname_entry.grid(column=4, row=550, sticky=EW)

        ttk.Label(self.mainframe, text="Department:").grid(column=1, row=600, sticky=E)
        self.division_combobox = ttk.Combobox(self.mainframe, width=31, state="readonly", textvariable=self.department_string)
        self.division_combobox['values'] = self.divisions
        self.division_combobox.current(0)
        self.division_combobox.grid(column=2, row=600, sticky=EW)

        ttk.Label(self.mainframe, text="Position:").grid(column=3, row=600, sticky=E)
        self.position_entry = ttk.Entry(self.mainframe, width=31, textvariable=self.position_string)
        self.position_entry.grid(column=4, row=600, sticky=EW)

        ttk.Label(self.mainframe, text="Email:").grid(column=1, row=650, sticky=E)
        self.email_entry = ttk.Entry(self.mainframe, width=31, textvariable=self.email_string)
        self.email_entry.grid(column=2, row=650, sticky=EW)

        ttk.Label(self.mainframe, text="Phone:").grid(column=3, row=650, sticky=E)
        self.phone_entry = ttk.Entry(self.mainframe, width=31, textvariable=self.phone_string)
        self.phone_entry.grid(column=4, row=650, sticky=EW)

        ttk.Label(self.mainframe, text="Building:").grid(column=1, row=700, sticky=E)
        self.building_combobox = ttk.Combobox(self.mainframe, width=31, state="readonly", textvariable=self.building_string)
        self.building_combobox['values'] = self.buildings
        self.building_combobox.current(0)
        self.building_combobox.grid(column=2, row=700, sticky=EW)

        ttk.Label(self.mainframe, text="Room:").grid(column=3, row=700, sticky=E)
        self.room_entry = ttk.Entry(self.mainframe, width=31, textvariable=self.room_string)
        self.room_entry.grid(column=4, row=700, sticky=EW)

        ttk.Separator(self.mainframe, orient=HORIZONTAL).grid(row=800, columnspan=5, sticky=EW)

        #
        # these are the elements of the Administration section of the UI
        ttk.Label(self.mainframe, text="Open in Jamf:").grid(column=1, row=850, sticky=E)
        ttk.Button(self.mainframe, text="Device", command=self.open_id_web).grid(column=2, row=850, sticky=W)
        ttk.Button(self.mainframe, text="User", command=self.open_user_web).grid(column=2, row=850)
        ttk.Button(self.mainframe, text="Search", command=self.open_search_web).grid(column=2, row=850, sticky=E)

        self.jamf_management_label = ttk.Label(self.mainframe, text="Managed by Jamf:                     ")
        self.jamf_management_label.grid(column=4, row=850, sticky=E)
        self.jamf_management_btn = ttk.Button(self.mainframe, text="True", width=6, command=lambda: self.jamf_management_btn.config(text="False") if self.jamf_management_btn.config('text')[-1] == 'True' else self.jamf_management_btn.config(text="True"))
        self.jamf_management_btn.grid(column=4, row=850, sticky=E)

        ttk.Separator(self.mainframe, orient=HORIZONTAL).grid(row=1000, columnspan=5, sticky=EW)

        self.status_label = ttk.Label(self.mainframe, textvariable=self.status_string)
        self.status_label.grid(column=1, row=1100, sticky=W, columnspan=4)

        ttk.Button(self.mainframe, text="Reset", width=6, command=self.reset_data).grid(column=4, row=1100, sticky=W)
        ttk.Button(self.mainframe, text="Quit", width=6, command=self.root.destroy).grid(column=4, row=1100)

        if access_level == 'full':
            self.submit_btn = ttk.Button(self.mainframe, text="Submit", default='active', command=self.submit)
            self.submit_btn.grid(column=4, row=1100, sticky=E)
        else:
            self.submit_btn = ttk.Button(self.mainframe, text="Auditing", state='disabled')
            self.submit_btn.grid(column=4, row=1100, sticky=E)

            self.computername_entry.configure(state='disabled')
            self.assettag_entry.configure(state='disabled')
            self.barcode_entry.configure(state='disabled')
            self.endusername_entry.configure(state='disabled')
            self.fullname_entry.configure(state='disabled')
            self.division_combobox.configure(state="disabled")
            self.position_entry.configure(state='disabled')
            self.email_entry.configure(state='disabled')
            self.phone_entry.configure(state='disabled')
            self.building_combobox.configure(state="disabled")
            self.room_entry.configure(state='disabled')

        #
        # this loop adds a small amount of space around each UI element, changing the value will significantly change the final size of the window
        for child in self.mainframe.winfo_children():
            child.grid_configure(padx=3, pady=3)

    def open_user_web(self):
        """
        Open currently displayed user record in jamf
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        #
        # in order to open the user in a browser you need the user's Jamf ID
        # in order to get the ID you need to open the user's record on Jamf
        if self.username_string.get():
            url = self.jamf_hostname + '/JSSResource/users/name/' + self.username_string.get()
            url = urllib.quote(url, ':/()')

            request = urllib2.Request(url)
            request.add_header('Accept', 'application/json')
            request.add_header('Authorization', 'Basic ' + base64.b64encode(self.jamf_username + ':' + self.jamf_password))

            response = urllib2.urlopen(request)
            response_json = json.loads(response.read())

            if response.code != 200:
                self.logger.error("%s: Invalid response code." % inspect.stack()[0][3])
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("%i returned." % response.code)
                return

            jss_user_id = response_json['user']['id']

        else:
            self.logger.error("%s: No user set." % inspect.stack()[0][3])
            self.status_label.configure(style='Warning.TLabel')
            self.status_string.set("No user set.")
            return

        if jss_user_id:
            url_formatted = self.jamf_hostname + "/users.html?id=" + str(jss_user_id) + "&o=r"
            webbrowser.open_new_tab(url_formatted)
            self.logger.info("%s: Opened user web. (%s)" % (inspect.stack()[0][3], self.username_string.get()))
            self.status_label.configure(style='Normal.TLabel')
            self.status_string.set("Opened URL for User.")

        else:
            self.logger.error("%s: No user id available." % inspect.stack()[0][3])
            self.status_label.configure(style='Warning.TLabel')
            self.status_string.set("No user available.")

    def open_id_web(self):
        """
        Open currently displayed computer record in jamf
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])
        if self.id_string.get():
            url_formatted = self.jamf_hostname + "/computers.html?id=" + self.id_string.get() + "&o=r"
            webbrowser.open_new_tab(url_formatted)
            self.logger.info("%s: Opened id web. (%s)" % (inspect.stack()[0][3], self.id_string.get()))
            self.status_label.configure(style='Normal.TLabel')
            self.status_string.set("Opened URL for ID.")

        else:
            self.logger.error("%s: No computer id available." % inspect.stack()[0][3])
            self.status_label.configure(style='Warning.TLabel')
            self.status_string.set("No ID available.")

    def open_search_web(self):
        """
        Open currently displayed search in jamf
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])
        if self.search_string.get():
            url_formatted = self.jamf_hostname + "/computers.html?queryType=Computers&query=*" + self.search_string.get() + "*"
            webbrowser.open_new_tab(url_formatted)
            self.logger.info("%s: Opened search web. (%s)" % (inspect.stack()[0][3], self.search_string.get()))
            self.status_label.configure(style='Normal.TLabel')
            self.status_string.set("Opened URL for search.")

        else:
            self.logger.error("%s: No search string available." % inspect.stack()[0][3])
            self.status_label.configure(style='Warning.TLabel')
            self.status_string.set("No search string entered.")

    def reset_user(self):
        """
        Reset user data structures to blank
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        self.username_string.set("")
        self.fullname_string.set("")
        self.department_string.set("")
        self.position_string.set("")
        self.email_string.set("")
        self.phone_string.set("")
        self.building_string.set("")
        self.room_string.set("")

    def reset_data(self):
        """
        reset all data structures to blank
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        if inspect.stack()[1][3] == "__call__":
            self.id_string.set("")
            self.search_string.set("")

        self.computer_name_string.set("")
        self.assettag_string.set("")
        self.barcode_string.set("")
        self.username_string.set("")
        self.fullname_string.set("")
        self.department_string.set("")
        self.position_string.set("")
        self.email_string.set("")
        self.phone_string.set("")
        self.building_string.set("")
        self.room_string.set("")

        self.status_label.configure(style='Normal.TLabel')
        self.status_string.set("Data reset.")

    def print_current_state(self):
        """
        Print current data structures, useful for debugging
        """

        self.logger.info("%s: activated" % inspect.stack()[0][3])

        print("Current user information")
        print("\tGeneral")
        print("\t\tComputer name : %s" % self.computer_name_string.get())
        print("\t\tAsset Tag     : %s" % self.assettag_string.get())
        print("\t\tBar code      : %s\n" % self.barcode_string.get())

        print("\tUser and Location")
        print("\t\tUsername      : %s" % self.username_string.get())
        print("\t\tFullname      : %s" % self.fullname_string.get())
        print("\t\tDepartment    : %s" % self.department_string.get())
        print("\t\tPosition      : %s" % self.position_string.get())
        print("\t\tEmail         : %s" % self.email_string.get())
        print("\t\tPhone         : %s" % self.phone_string.get())
        print("\t\tBuilding      : %s" % self.building_string.get())
        print("\t\tRoom          : %s\n" % self.room_string.get())

        print("Other :")
        print("\tJamf ID : %s" % self.id_string.get())
        print("\tStatus  : %s\n" % self.status_string.get())

        return

    def log_current_state(self):
        """
        log current data structures, useful for debugging
        """

        self.logger.info("%s: activated" % inspect.stack()[0][3])

        self.logger.info("Current user information")
        self.logger.info("\tGeneral")
        self.logger.info("\t\tComputer name : %s" % self.computer_name_string.get())
        self.logger.info("\t\tAsset Tag     : %s" % self.assettag_string.get())
        self.logger.info("\t\tBar code      : %s" % self.barcode_string.get())

        self.logger.info("\tUser and Location")
        self.logger.info("\t\tUnsername     : %s" % self.username_string.get())
        self.logger.info("\t\tFullname      : %s" % self.fullname_string.get())
        self.logger.info("\t\tDepartment    : %s" % self.department_string.get())
        self.logger.info("\t\tPosition      : %s" % self.position_string.get())
        self.logger.info("\t\tEmail         : %s" % self.email_string.get())
        self.logger.info("\t\tPhone         : %s" % self.phone_string.get())
        self.logger.info("\t\tBuilding      : %s" % self.building_string.get())
        self.logger.info("\t\tRoom          : %s" % self.room_string.get())

        self.logger.info("Other :")
        self.logger.info("\tJamf ID : %s" % self.id_string.get())
        self.logger.info("\tStatus  : %s" % self.status_string.get())

    def check_submit(self):
        """
        precheck required fields for valid content
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        #
        # if you plan on adding additional fields, you'll likely want to add them to this
        # method to be sure they contain valid values before submitting.
        bad_fields = []

#         if not self.assettag_string.get():
#             bad_fields.append("Asset Tag")

        if not self.id_string.get():
            bad_fields.append("Jamf ID")

        if not self.username_string.get():
            bad_fields.append("Username")

        if not self.fullname_string.get():
            bad_fields.append("Full Name")

        if not bad_fields:
            # We're good.
            self.logger.warn("%s: No fields reported." % inspect.stack()[0][3])
            return True
        else:
            self.logger.warn("%s: Bad fields reported: %r" % (inspect.stack()[0][3], bad_fields))
            if len(bad_fields) >= 5:
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Many empty fields!")
                return False
            else:
                bad_fields = ", ".join(bad_fields)
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Empty fields: %s" % bad_fields)
                return False

    def submit(self):
        """
        submit current data structures to jamf
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        if not self.check_submit():
            return

        try:
            self.status_label.configure(style='Normal.TLabel')
            self.status_string.set("Submitting...")

            jamf_url = self.jamf_hostname + '/JSSResource/computers/id/' + self.id_string.get()

            #
            # These are the individual fields associated with UI elements
            # If you add additional fields to the UI, you will need to add corresponding
            # XML elements form them to be submitted back to the Jamf database.
            top = ET.Element('computer')

            general = ET.SubElement(top, 'general')

            computer_name_xml = ET.SubElement(general, 'name')
            computer_name_xml.text = self.computer_name_string.get()

            asset_tag_xml = ET.SubElement(general, 'asset_tag')
            asset_tag_xml.text = self.assettag_string.get()

            barcode_xml = ET.SubElement(general, 'barcode_1')
            barcode_xml.text = self.barcode_string.get()

            location = ET.SubElement(top, 'location')

            username_xml = ET.SubElement(location, 'username')
            username_xml.text = self.username_string.get()

            email_xml = ET.SubElement(location, 'email_address')
            email_xml.text = self.email_string.get()

            realname_xml = ET.SubElement(location, 'real_name')
            realname_xml.text = self.fullname_string.get()

            phone_xml = ET.SubElement(location, 'phone')
            phone_xml.text = self.phone_string.get()

            building_xml = ET.SubElement(location, 'building')
            building_xml.text = self.building_string.get()

            room_xml = ET.SubElement(location, 'room')
            room_xml.text = self.room_string.get()

            position_xml = ET.SubElement(location, 'position')
            position_xml.text = self.position_string.get()

            department_xml = ET.SubElement(location, 'department')
            department_xml.text = self.department_string.get()

            #
            # these are the fields that enable removing machines
            # from management quotas.
#             if self.jamf_management_btn.config('text')[-1] == 'True'
#                 remote_management = ET.SubElement(general, 'remote_management')
#                 managed_xml       = ET.SubElement(remote_management, 'managed')
#                 managed_xml.text  = 'true'
#             else
#                 remote_management = ET.SubElement(general, 'remote_management')
#                 managed_xml       = ET.SubElement(remote_management, 'managed')
#                 managed_xml.text  = 'false'

            self.log_current_state()
            self.logger.info("%s: submitting \n%s" % (inspect.stack()[0][3], ET.tostring(top)))

#             print(ET.tostring(top))

            #
            # comminicating with the Jamf database and putting the XML structure
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            request = urllib2.Request(jamf_url, data=ET.tostring(top))
            base64string = base64.b64encode('%s:%s' % (self.jamf_username, self.jamf_password))
            request.add_header("Authorization", "Basic %s" % base64string)
            request.add_header('Content-Type', 'text/xml')
            request.get_method = lambda: 'PUT'
            response = opener.open(request)

            self.logger.info("%s: submitted." % inspect.stack()[0][3])
            self.status_label.configure(style='Normal.TLabel')
            self.status_string.set(str(response.code) + " Submitted.")
            return

        except urllib2.HTTPError, error:
            if error.code == 400:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Request error."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Request error."))
            elif error.code == 401:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Authorization error."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Authorization error."))
            elif error.code == 403:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Permissions error."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Permissions error."))
            elif error.code == 404:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Resource not found."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Resource not found."))
            elif error.code == 409:
                contents = error.read()
                error_message = re.findall(r"Error: (.*)<", contents)
                print("HTTP code %i: %s %s %s" % (error.code, "Resource conflict.", error_message[0], self.id_string.get()))
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Resource conflict. " + error_message[0]))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Resource conflict. " + error_message[0]))
            else:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Generic error."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Generic error."))
            return
        except urllib2.URLError, error:
            self.logger.error("%s: Error contacting JSS." % (inspect.stack()[0][3]))
            self.status_label.configure(style='Warning.TLabel')
            self.status_string.set("Error contacting JSS.")
            return
        except Exception as exception_message:
            self.logger.error("%s: Error submitting to Jamf. [%s]" % (inspect.stack()[0][3], exception_message))
            self.status_label.configure(style='Warning.TLabel')
            self.status_string.set("Error submitting to Jamf. [%s]" % exception_message)
            return

    def usage(self):
        """
        Calculate which valid user uses this computer the most
        """
        #
        # this method uses the pexpect module, if you have issues with the module you'll need to remove this method.
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        try:
            #
            # aquire admin password
            password = tkSimpleDialog.askstring("Password", "Enter admin password:", show='*', parent=self.root)

            if not password:
                self.logger.error("%s: Canceled Top User." % (inspect.stack()[0][3]))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Canceled Top User.")
                return

            cmd_output = []
            try:
                #
                # utilizing the
                child = pexpect.spawn('bash', ['-c', '/usr/bin/sudo -k /usr/sbin/ac -p'])

                exit_condition = False
                while not exit_condition:
                    result = child.expect(['\n\nPass', 'Password:', 'sudo', pexpect.EOF, pexpect.TIMEOUT])

                    cmd_output.append(child.before)
                    cmd_output.append(child.after)
                    if result == 0:
                        child.sendline(password)
                    elif result == 1:
                        child.sendline(password)
                    elif result == 2:
                        self.status_label.configure(style='Warning.TLabel')
                        self.status_string.set("Incorrect admin password.")
                        return
                    elif result == 3:
                        exit_condition = True
                    elif result == 4:
                        exit_condition = True
                    else:
                        print("Unknown error. Exiting.")
                        exit_condition = True

            except Exception as exception_message:
                self.logger.error("%s: Unknown error. [%s]" % (inspect.stack()[0][3], exception_message))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Error submitting to Jamf. [%s]" % exception_message)
                return

            #
            # begin parsing out useful content
            checked_output = []
            for index, content in enumerate(cmd_output):
                if isinstance(content, basestring):
                    if "System\r\nAdministrator." in content:
                        pass
                    elif not content:
                        pass
                    elif content == "Password:":
                        pass
                    else:
                        checked_output.append(content)

            #
            # begin parsing out users and time data from output
            users_raw = []
            for super_item in checked_output:
                sub_item = super_item.split("\r\n")
                for user in sub_item:
                    if user:
                        user = user.strip()
                        users_raw.append(user)

            users = [item for item in users_raw if item]

            grid = {}

            #
            # build dictionary of output
            for item in users:
                match = re.search(r'^(\w*)\s*(\d*.\d*)', item)
                grid[match.group(1)] = match.group(2)

            login_total = float(grid['total'])

            #
            # remove various admin/management accounts
            try:
                del grid['total']
            except Exception:
                pass

            try:
                del grid['admin']
            except Exception:
                pass

            try:
                del grid['root']
            except Exception:
                pass

            try:
                del grid['_mbsetupuser']
            except Exception:
                pass

            try:
                del grid['radmind']
            except Exception:
                pass

            try:
                del grid['Guest']
            except Exception:
                pass

            #
            # calculate time percentages of remaining users
            for item in grid:
                temp = float(grid[item])
                grid[item] = temp / login_total

            # sort the remaining users, based on percentage
            grid_sorted = sorted(grid, key=grid.__getitem__, reverse=True)

            #
            # if there are still valid users, continue
            if grid_sorted:

                #
                # select the top user.
                self.username_string.set(grid_sorted[0])
                high_user_percentge = int(grid[grid_sorted[0]] * 100)
                self.logger.info("%s: %s selected." % (inspect.stack()[0][3], self.username_string.get()))
                self.status_label.configure(style='Normal.TLabel')
                self.status_string.set(str(high_user_percentge) + "% user selected.")
                return
            else:
                self.logger.error("%s: Error selecting highest usage user, no eligible users." % (inspect.stack()[0][3]))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Error selecting highest usage user, no eligible users")
                return

        except ValueError:
            self.logger.error("%s: Error setting Usage Mode." % (inspect.stack()[0][3]))
            self.status_label.configure(style='Warning.TLabel')
            self.status_string.set("Error setting Usage Mode.")
            return

    def button_state(self):
        """
        sets buttons to the correct state
        """

        #
        # This method is used to enable/disable specific buttons, based on OS, etc.
        #
        # You want to use the Combobox option of state='disabled'.
        #
        # There are three options for state as follows:
        #
        #     state='normal' which is the fully functional Combobox.
        #     state='readonly' which is the Combobox with a value, but can't be changed (directly).
        #     state='disabled' which is where the Combobox cannot be interacted with.
        #
        # self.highlight_button = ttk.Style()
        # self.highlight_button.configure('Highlight.TButton', foreground='red')
        # ttk.Button(self.mainframe, text="Query this system", style='Highlight.TButton', command= lambda: self.query_jamf_me()).grid(column=2, row=20, padx =3, sticky=W)

        self.logger.info("%s: activated" % inspect.stack()[0][3])

        if self.platform == "Mac" and self.access_level == 'full':
            self.jamf_management_btn.configure(state="normal")

        else:
            self.jamf_management_btn.configure(state="disabled")

    def query_jamf_id(self):
        """
        query jamf for specific computer record
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])
        self.reset_data()

        try:

            self.status_label.configure(style='Normal.TLabel')
            self.status_string.set("ID Mode selected.")

            #
            # request specific jamf computer record
            url = self.jamf_hostname + '/JSSResource/computers/id/' + self.id_string.get()
            request = urllib2.Request(url)
            request.add_header('Accept', 'application/json')
            request.add_header('Authorization', 'Basic ' + base64.b64encode(self.jamf_username + ':' + self.jamf_password))

            response = urllib2.urlopen(request)
            response_json = json.loads(response.read())

            if response.code != 200:
                self.logger.error("%s: Error from jss" % inspect.stack()[0][3])
                self.status_string.set("%i returned." % response.code)
                return

            #
            # begin populating display strings
            self.computer_name_string.set(response_json['computer']['general']['name'])
            self.assettag_string.set(response_json['computer']['general']['asset_tag'])
            self.barcode_string.set(response_json['computer']['general']['barcode_1'])
            self.username_string.set(response_json['computer']['location']['username'])

            self.email_string.set(response_json['computer']['location']['email_address'])
            self.fullname_string.set(response_json['computer']['location']['real_name'])
            self.phone_string.set(response_json['computer']['location']['phone'])
            self.room_string.set(response_json['computer']['location']['room'])
            self.building_string.set(response_json['computer']['location']['building'])
            self.position_string.set(response_json['computer']['location']['position'])
            self.department_string.set(response_json['computer']['location']['department'])
            self.platform = response_json['computer']['general']['platform']

            self.jamf_management = response_json['computer']['general']['remote_management']['managed']

            if self.jamf_management is True:
                self.jamf_management_btn.configure(text="True")
            elif self.jamf_management is False:
                self.jamf_management_btn.configure(text="False")
            else:
                print("else Jamf managment: %r" % self.jamf_management)

            #
            # if you desire to add EA's you will need to find each by parsing all of the EA's
            #

            # jss_purpose_raw = response_json['computer']['extension_attributes']
            # for ea in jss_purpose_raw:
            #     if ea['name'] == 'EA1':
            #         self.ea1_string.set(ea['value'])
            #     elif ea['name'] == 'EA2':
            #         self.ea2_string.set(ea['value'])
            #     elif ea['name'] == 'EA3':
            #         self.ea3_string.set(ea['value'])
            #
            #  etc
            #

            self.log_current_state()

        #
        # handle communication errors
        except urllib2.HTTPError, error:
            if error.code == 400:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Request error."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Request error."))
            elif error.code == 401:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Authorization error."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Authorization error."))
            elif error.code == 403:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Permissions error."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Permissions error."))
            elif error.code == 404:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Resource not found."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Resource not found."))
            elif error.code == 409:
                contents = error.read()
                error_message = re.findall(r"Error: (.*)<", contents)
                print("HTTP code %i: %s %s %s" % (error.code, "Resource conflict.", error_message[0], self.id_string.get()))
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Resource conflict. " + error_message[0]))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Resource conflict. " + error_message[0]))
            else:
                self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Generic error."))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("HTTP code %i: %s" % (error.code, "Generic error."))
            return
        except urllib2.URLError, error:
            self.logger.error("%s: Error contacting JSS." % (inspect.stack()[0][3]))
            self.status_label.configure(style='Warning.TLabel')
            self.status_string.set("Error contacting JSS.")
            return
        except Exception as exception_message:
            self.logger.error("%s: Error submitting to Jamf. [%s]" % (inspect.stack()[0][3], exception_message))
            self.status_label.configure(style='Warning.TLabel')
            self.status_string.set("Error submitting to Jamf. [%s]" % exception_message)
            return

        self.status_label.configure(style='Normal.TLabel')
        self.status_string.set("Jamf returned info for ID %s." % self.id_string.get())
        self.button_state()

    def query_jamf_me(self):
        """
        Query jamf about this particular machine
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        #
        # this method finds the UUID for the local machine
        # query's jamf and parses the ID from the record
        # and then calls the main query method
        # it's wasteful the first time it's called.
        if not self.local_jamf_id:

            if platform.system() == 'Darwin':
                local_uuid_raw = subprocess.check_output(["system_profiler", "SPHardwareDataType"])
                local_uuid = re.findall(r'Hardware UUID: (.*)', local_uuid_raw)[0]
            elif platform.system() == 'Windows':
                local_uuid_raw = subprocess.check_output("wmic CsProduct Get UUID")
                local_uuid_raw = local_uuid_raw.split("\r\r\n")[1]
                local_uuid = local_uuid_raw.split(" ")[0]
            else:
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Missing native UUID discovery.")
                return

            #
            # communicate with Jamf server
            try:
                url = self.jamf_hostname + '/JSSResource/computers/udid/' + local_uuid
                request = urllib2.Request(url)
                request.add_header('Accept', 'application/json')
                request.add_header('Authorization', 'Basic ' + base64.b64encode(self.jamf_username + ':' + self.jamf_password))

                response = urllib2.urlopen(request)
                response_json = json.loads(response.read())

                #
                # a non-200 response is bad, report and return
                if response.code != 200:
                    self.logger.error("%s: Error from jss" % inspect.stack()[0][3])
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("%i returned." % response.code)
                    return

                self.local_jamf_id = response_json['computer']['general']['id']
                self.id_string.set(self.local_jamf_id)

            #
            # handle various communication errors
            except urllib2.HTTPError, error:
                if error.code == 400:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Request error."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Request error."))
                elif error.code == 401:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Authorization error."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Authorization error."))
                elif error.code == 403:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Permissions error."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Permissions error."))
                elif error.code == 404:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Resource not found."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Resource not found."))
                elif error.code == 409:
                    contents = error.read()
                    error_message = re.findall(r"Error: (.*)<", contents)
                    print("HTTP code %i: %s %s %s" % (error.code, "Resource conflict.", error_message[0], self.id_string.get()))
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Resource conflict. " + error_message[0]))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Resource conflict. " + error_message[0]))
                else:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Generic error."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Generic error."))
                return
            except urllib2.URLError, error:
                self.logger.error("%s: Error contacting JSS." % (inspect.stack()[0][3]))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Error contacting JSS.")
                return
            except Exception as exception_message:
                self.logger.error("%s: Error submitting to Jamf. [%s]" % (inspect.stack()[0][3], exception_message))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Error submitting to Jamf. [%s]" % exception_message)
                return

        else:
            self.logger.info("%s: local jamf id %r" % (inspect.stack()[0][3], self.local_jamf_id))
            self.id_string.set(self.local_jamf_id)

        self.query_jamf_id()

    def populate_menu(self, menu_choice):
        """
        builds list from static data source in jamf
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        #
        # this method builds lists that can then be used to build combobox or popup menus from
        # departments, buildings, sites
        url = self.jamf_hostname + '/JSSResource/' + menu_choice
        request = urllib2.Request(url)
        request.add_header('Accept', 'application/json')
        request.add_header('Authorization', 'Basic ' + base64.b64encode(self.jamf_username + ':' + self.jamf_password))

        response = urllib2.urlopen(request)
        response_json = json.loads(response.read())

        if response.code != 200:
            self.logger.error("%s: Error from jss" % inspect.stack()[0][3])
            return

        menu_items = ['None']
        for item in response_json[menu_choice]:
            menu_items.append(item.get('name'))
        self.logger.info("%s: built menu: %r" % (inspect.stack()[0][3], menu_items))
        return menu_items

    def populate_ea_menu(self, ea_id):
        """
        builds list from extension attribute in jamf
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        #
        # this method builds lists that can then be used to build combobox or popup menus from EA's
        url = self.jamf_hostname + '/JSSResource/computerextensionattributes/id/' + str(ea_id)
        request = urllib2.Request(url)
        request.add_header('Accept', 'application/json')
        request.add_header('Authorization', 'Basic ' + base64.b64encode(self.jamf_username + ':' + self.jamf_password))

        response = urllib2.urlopen(request)
        response_json = json.loads(response.read())

        if response.code != 200:
            self.logger.error("%s: Error from jss" % inspect.stack()[0][3])
            return

        choices = response_json['computer_extension_attribute']['input_type']['popup_choices']
        choices = ['None'] + choices
        self.logger.info("%s: built ea: %r" % (inspect.stack()[0][3], choices))
        return choices

    def search_string_jamf(self):
        """
        This method handles searching Jamf with a string
        """
        self.logger.info("%s: activated" % inspect.stack()[0][3])

        def double_click(*event):
            """
            handle clicks
            """

            #
            # when a click occurs, parse out ID from string and call query method
            selected = listbox.get(listbox.curselection())
            trim_select = re.search(r'\((.*)\)', selected).group(1)

            self.id_string.set(trim_select)
            self.query_jamf_id()

            self.root.lift()

        self.reset_data()

        if self.search_string.get() == "" or self.search_string.get().replace(" ", "") == "":
            if self.id_string.get():
                self.query_jamf_id()
                self.status_label.configure(style='Normal.TLabel')
                self.status_string.set("Searched for ID.")
                self.logger.info("%s: searched for ID: %r" % (inspect.stack()[0][3], self.id_string.get()))
            else:
                self.logger.error("%s: No search string" % inspect.stack()[0][3])
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("No search string entered.")

        else:
            self.id_string.set("")
            self.logger.info("%s: searched for string: %r" % (inspect.stack()[0][3], self.search_string.get()))

            #
            # erase previous displayed values
#             self.reset_data()

            #
            # encode special characters included in search string
            url = self.jamf_hostname + '/JSSResource/computers/match/' + urllib.quote('*' + self.search_string.get() + '*')
            self.logger.info("%s: searched with url: %r" % (inspect.stack()[0][3], url))

            #
            # communicate with Jamf server
            try:
                request = urllib2.Request(url)
                request.add_header('Accept', 'application/json')
                request.add_header('Authorization', 'Basic ' + base64.b64encode(self.jamf_username + ':' + self.jamf_password))

                response = urllib2.urlopen(request)
                try:
                    response_json = json.loads(response.read())
                except Exception as exception_message:
                    self.logger.error("issue parsing JSON: %r" % exception_message)
                    return
                #
                # a non-200 response is bad, report and return
                if response.code != 200:
                    self.logger.error("%s: error from jss" % inspect.stack()[0][3])
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("%i returned." % response.code)
                    return

            #
            # handle various communication errors
            except urllib2.HTTPError, error:
                if error.code == 400:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Request error."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Request error."))
                elif error.code == 401:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Authorization error."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Authorization error."))
                elif error.code == 403:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Permissions error."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Permissions error."))
                elif error.code == 404:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Resource not found."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Resource not found."))
                elif error.code == 409:
                    contents = error.read()
                    error_message = re.findall(r"Error: (.*)<", contents)
                    print("HTTP code %i: %s %s %s" % (error.code, "Resource conflict.", error_message[0], self.id_string.get()))
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Resource conflict. " + error_message[0]))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Resource conflict. " + error_message[0]))
                else:
                    self.logger.error("%s: HTTP code %i: %s" % (inspect.stack()[0][3], error.code, "Generic error."))
                    self.status_label.configure(style='Warning.TLabel')
                    self.status_string.set("HTTP code %i: %s" % (error.code, "Generic error."))
                return
            except urllib2.URLError, error:
                self.logger.error("%s: Error contacting JSS." % (inspect.stack()[0][3]))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Error contacting JSS.")
                return
            except Exception as exception_message:
                self.logger.error("%s: Error submitting to Jamf. [%s]" % (inspect.stack()[0][3], exception_message))
                self.status_label.configure(style='Warning.TLabel')
                self.status_string.set("Error submitting to Jamf. [%s]" % exception_message)
                return

            #
            # begin parsing data returned from Jamf
            self.status_label.configure(style='Normal.TLabel')
            self.status_string.set("%i matches returned." % len(response_json['computers']))
            self.logger.info("%s: %r" % (inspect.stack()[0][3], self.status_string.get()))

            search_font = tkFont.Font(font='TkDefaultFont')
            match_results = []
            max_length = 0
            #
            # parse each returned computer element, retaining Jamf ID and Computer name
            # properly format value to display
            # build a version of the computer name used to sort by
            #  these rules are for our environment and may have no effect in yours.
            #  if the name is in the format "labmac-1" the integer is expanded to -0001
            #  if the name is in the format "[lost] labmac-1" the sorting name is stored as
            #    "labmac-1a" to differentiate it from "labmac-1"
            # the values are added to a list containing the previously processed values as
            #   [sorting name, computer name, jamf id]
            for node in response_json['computers']:
                match_id = node['id']
                match_name = node['name']
                if not match_name:
                    match_name = "Not named."

                name_trim = match_name

                try:
                    number_part = re.search(r'(\d+)', name_trim).group(1)
                    number_free = "".join([i for i in name_trim if not i.isdigit()])
                    expanded_number = '{:04d}'.format(int(number_part))
                    expanded_x = number_free + expanded_number
                    name_trim = expanded_x
                except:
                    pass

                if "[" in name_trim:
                    name_trim = re.search(r']([ -]*)(.*)', name_trim).group(2)
                    name_trim = str(name_trim) + "a"

                match_results.append([name_trim, match_name, match_id])
                (string_width, string_height) = (search_font.measure(match_name + " (" + str(match_id) + ")"), search_font.metrics("linespace"))
                if max_length < string_width:
                    max_length = string_width

            #
            # if there were returned results, build and display search results window
            #
            #
            # position results window next to the main window, even if it has moved
            #  from the original location
            # while sorting the list based on the synthetic string,
            #  display the computer name and ID
            # bind clicks to function
            if match_results:

                search_window = Toplevel()

                split_geom = self.root.winfo_geometry().split("+")
                r_h = int(split_geom[0].split("x")[0])
                r_pos_x = int(split_geom[1])
                r_pos_y = int(split_geom[2])
                string_width = int(max_length + 22)

                search_window_geo = "%ix%i+%i+%i" % (string_width, 400, (r_h + r_pos_x + 10), (r_pos_y))
                search_window.geometry(search_window_geo)

                search_window.title("Search results")

                list_frame = ttk.Frame(search_window, width=string_width, height=400, padding=(4, 0, 0, 0))

                scrollbar = Scrollbar(list_frame)
                scrollbar.pack(side=RIGHT, fill=Y)

                listbox = Listbox(list_frame, bd=0, yscrollcommand=scrollbar.set, selectmode=SINGLE, width=190, height=400)
                listbox.pack()

                scrollbar.config(command=listbox.yview)

                list_frame.pack()

                for item in sorted(match_results):
                    insert_string = item[1] + " (" + str(item[2]) + ")"
                    listbox.insert(END, insert_string)

#                 self.saved_results.append((self.search_string.get(), match_results))

                listbox.bind("<<ListboxSelect>>", double_click)

                search_window.mainloop()


def login(logger):
    """
    if the user has proper privleges, consider them an authorized user and proceed
    """
    def read_create_prefs(logger):
        """
        Read specified config file or create default data structure
        """
        logger.info("%s: activated" % inspect.stack()[0][3])
        config_path = ''

        executable_name = os.path.basename(sys.argv[0])

        if executable_name.count('.') > 1:
            filename = executable_name.split('.')[:-1]
            filename = '.'.join(filename)
        else:
            filename = executable_name.split('.')[0]

        try:
            if '_' in filename:
                split_filename = filename.split('_')
                try:
                    int(split_filename[-1][0])
                    del split_filename[-1]
                except Exception as exception_message:
                    print(exception_message)
                config_name = 'edu.scl.utah.' + '_'.join(split_filename) + '.ini'
            else:
                config_name = 'edu.scl.utah.' + filename + '.ini'

        except Exception as exception_message:
            logger.error("Error creating config_name [%s]. %s" % (executable_name, exception_message))
            return '', ''

        if platform.system() == 'Darwin':
            if os.path.exists(pwd.getpwuid(os.getuid())[5] + os.path.join('/', 'Library', 'Preferences', config_name)):
                config_path = pwd.getpwuid(os.getuid())[5] + os.path.join('/', 'Library', 'Preferences', config_name)
            elif os.path.exists(os.path.join('/', 'Library', 'Preferences', config_name)):
                config_path = os.path.join('/', 'Library', 'Preferences', config_name)
            else:
                config_path = pwd.getpwuid(os.getuid())[5] + os.path.join('/', 'Library', 'Preferences', config_name)

        elif platform.system() == 'Windows':
            config_path = os.path.join(os.environ['APPDATA'], config_name)

        if not os.path.exists(config_path):
            logger.warn("Configuration file not found, creating structure in memory.")
            config_file = ConfigParser.SafeConfigParser(allow_no_value=True)
            config_file.add_section('login')
            config_file.set('login', 'hosts', 'https://new_server:8443')
            config_file.set('login', 'username', '')

        else:
            config_file = ConfigParser.SafeConfigParser(allow_no_value=True)
            try:
                config_file.read(config_path)
            except Exception as exception_message:
                logger.error("Error reading pre-exiting configuration file [%s]. %s" % (config_path, exception_message))
                config_file = ConfigParser.SafeConfigParser(allow_no_value=True)
                config_file.add_section('login')
                config_file.set('login', 'hosts', 'https://new_server:8443')
                config_file.set('login', 'username', '')

        logger.info("Configuration path: %s" % config_path)
        return config_file, config_path

    def injest_prefs(logger, configfile):
        """
        Create data structures from config file
        """
        logger.info("%s: activated" % inspect.stack()[0][3])
        config_options = {}
        config_options["login"] = {}

        for section in ["login"]:
            for item in configfile.options(section):
                if "use_" in item:
                    try:
                        config_options[section][item] = configfile.getboolean(section, item)
                    except:
                        config_options[section][item] = False
                elif "path" in item:
                    config_options[section][item] = configfile.get(section, item)
                else:
                    config_options[section][item] = configfile.get(section, item)

        logger.info("Configuration file variables:")
        for key, value in config_options.items():
            logger.info(key)
            for sub_key, sub_value in value.items():
                logger.info("\t%s %r" % (sub_key, sub_value))

        return config_options["login"]["hosts"]

    def modify_prefs(logger, config_file, config_path, hostnames, valid_host):
        """
        Convert data structures back into config file and write out changes.
        """
        logger.info("%s: activated" % inspect.stack()[0][3])

        hostnames.remove("https://new_server:8443")

        if valid_host not in hostnames:
            logger.info("%s not in configuration file, adding." % valid_host)
            hostnames.append(valid_host)
            config_file.set('login', 'hosts', ",".join(hostnames))

            try:
                with open(config_path, "wb") as config_write:
                    config_file.write(config_write)
                    logger.info("Wrote configuration file at %s." % config_path)
            except Exception as exception_message:
                logger.error("Error writing configuration file [%s]. %s" % (config_path, exception_message))

    def try_login():
        """
        jamf api call for login test
        """

        def call_jss(logger, api_call):
            """
            consolidate API calls to single function
            pass in logger and api call.
            """
            logger.info("%s: activated" % inspect.stack()[0][3])

            try:
                url = jamf_hostname.get() + '/JSSResource/' + api_call

                logger.info("%s called with %s" % (inspect.stack()[0][3], api_call))

                request = urllib2.Request(url)
                request.add_header('Accept', 'application/json')
                request.add_header('Authorization', 'Basic ' + base64.b64encode(jamf_username.get() + ':' + jamf_password.get()))

                response = urllib2.urlopen(request)

                logger.info("Code returned: %s %s" % (response.code, api_call))

                if response.code != 200:
                    logger.error("login: Invalid response from Jamf (" + api_call + ")")
                    tkMessageBox.showerror("Jamf login", "Invalid response from Jamf")
                    root.destroy() # clean up after yourself!
                    sys.exit()

                response_json = json.loads(response.read())

                return response_json

            #
            # handle various communication errors
            except urllib2.HTTPError, error:
                if error.code == 401:
                    logger.error("%s: Invalid username or password. (%r) (%s)" % (inspect.stack()[0][3], jamf_username.get(), api_call))
                    tkMessageBox.showerror("Jamf login", "Invalid username or password.")
                elif error.code == 404:
                    logger.warn("%s: JSS account not found. [%s]" % (inspect.stack()[0][3], jamf_username.get()))
                    return None
                else:
                    logger.error("%s: Error communicating with JSS. %s %s" % (inspect.stack()[0][3], jamf_hostname.get(), api_call))
                    tkMessageBox.showerror("Jamf login", "HTTP error from:\n%s" % jamf_hostname.get())
            except urllib2.URLError:
                logger.error("%s: Error contacting JSS: %s %s" % (inspect.stack()[0][3], jamf_hostname.get(), api_call))
                tkMessageBox.showerror("Jamf login", "Unable to contact:\n%s" % jamf_hostname.get())
            except Exception as exception_message:
                # this could be so many different things... :(
                logger.error("%s: Generic error. (%r) %s" % (inspect.stack()[0][3], exception_message, api_call))
                tkMessageBox.showerror("Jamf login", "Generic error from %s." % jamf_hostname.get())

            #
            # handle bad condition exits here...
            logger.error("%s: Exiting, Error calling %s" % (inspect.stack()[0][3], api_call))
            sys.exit()

        logger.info("%s: activated" % inspect.stack()[0][3])

        valid_user_read = False
        valid_user_full = False
        global access_level

        try:

            jss_accounts = call_jss(logger, 'accounts')

            raw_ldap = call_jss(logger, 'ldapservers')
            ldap_servers = raw_ldap['ldap_servers']
            logger.info("JSS LDAP servers: %r" % ldap_servers)

            #
            # store list of user and group privileges
            user_list = jss_accounts['accounts']['users']
            group_list = jss_accounts['accounts']['groups']

            #
            # find groups on jss that have required_privileges
            valid_full_groups = []
            valid_read_groups = []

            for item in group_list:
                missing_ldap_read_privileges = []
                missing_ldap_update_privileges = []
                valid_ldap_read = False
                valid_ldap_update = False

                raw_privs = call_jss(logger, 'accounts/groupid/' + str(item['id']))
                this_group_privs = raw_privs['group']['privileges']['jss_objects']

                for read_item in read_privileges:
                    if read_item not in this_group_privs:
                        missing_ldap_read_privileges.append(read_item)
                if not missing_ldap_read_privileges:
                    valid_ldap_read = True

                for update_item in update_privileges:
                    if update_item not in this_group_privs:
                        missing_ldap_update_privileges.append(update_item)
                if not missing_ldap_update_privileges:
                    valid_ldap_update = True

                if valid_ldap_read and valid_ldap_update:
                    logger.info("%s is read and update valid." % item['name'])
                    valid_full_groups.append([item['id'], item['name']])

                elif valid_ldap_read:
                    logger.info("%s is read valid." % item['name'])
                    valid_read_groups.append([item['id'], item['name']])
                    logger.warn("login: Group %r lacks appropriate update privileges: %r" % (item['name'], (missing_ldap_read_privileges + missing_ldap_update_privileges)))

                else:
                    logger.error("login: Group %r lacks appropriate privileges: %r" % (item['name'], missing_ldap_read_privileges + missing_ldap_update_privileges))

            #
            # find servers with valid groups the user is a member of
            valid_full_servers = []
            valid_read_servers = []

            for server in ldap_servers:
                for group in valid_full_groups:
                    raw_group_membership = call_jss(logger, 'ldapservers/id/' + str(server['id']) + '/group/' + urllib.quote(str(group[1])) + '/user/' + jamf_username.get())

                    if raw_group_membership['ldap_users']:
                        logger.info("login: %s is a member of full group %s on server %s" % (jamf_username.get(), group[1], server['name']))
                        valid_full_servers.append(server['name'])

                for group in valid_read_groups:
                    raw_group_membership = call_jss(logger, 'ldapservers/id/' + str(server['id']) + '/group/' + urllib.quote(str(group[1])) + '/user/' + jamf_username.get())

                    if raw_group_membership['ldap_users']:
                        logger.info("login: %s is a member of read group %s on server %s" % (jamf_username.get(), group[1], server['name']))
                        valid_read_servers.append(server['name'])

            #
            # Check user's privileges
            user_update = False
            user_read = False
            missing_read_privileges = []
            missing_update_privileges = []
            try:
                raw_privileges = call_jss(logger, 'accounts/username/' + jamf_username.get())

                if raw_privileges:
                    user_privileges = raw_privileges['account']['privileges']['jss_objects']

                    for item in read_privileges:
                        if item not in user_privileges:
                            missing_read_privileges.append(item)

                    if not missing_read_privileges:
                        user_read = True

                    for item in update_privileges:
                        if item not in user_privileges:
                            missing_update_privileges.append(item)

                    if not missing_update_privileges:
                        user_update = True

                    if missing_read_privileges or missing_update_privileges:
                        logger.warn("login: %s is missing privileges for full access: %r" % (jamf_username.get(), missing_read_privileges + missing_update_privileges))

            except Exception as exception_message:
                logger.warn("%s: Error checking user account info. (%r)" % (inspect.stack()[0][3], exception_message))

            #
            # if all require privileges accounted for, proceed
            # else alert and fail
            if user_read and user_update:
                logger.info("login: valid full user login. (%r)" % jamf_username.get())
                root.destroy()  # clean up after yourself!
                access_level = 'full'
                return
            elif valid_full_servers:
                logger.info("login: valid full LDAP login. (%r)" % jamf_username.get())
                root.destroy()  # clean up after yourself!
                access_level = 'full'
                return
            elif user_read:
                logger.info("login: valid read user login. (%r)" % jamf_username.get())
                root.destroy()  # clean up after yourself!
                access_level = 'read-only'
                return
            elif valid_read_servers:
                logger.info("login: valid read LDAP login. (%r)" % jamf_username.get())
                root.destroy()  # clean up after yourself!
                access_level = 'read-only'
                return
            else:
                logger.error("login: User %r lacks appropriate privileges: %r" % (jamf_username.get(), missing_privileges))
                tkMessageBox.showerror("Jamf login", "User lacks appropriate privileges.\n%r" % missing_privileges)

        #
        # handle various communication errors
        except urllib2.HTTPError, error:

            logger.info("Code returned: %s" % error.code)

            if error.code == 401:
                logger.error("%s: Invalid username or password. (%r)" % (inspect.stack()[0][3], jamf_username.get()))
                tkMessageBox.showerror("Jamf login", "Invalid username or password.")
            else:
                logger.error("%s: Error communicating with JSS. %s" % (inspect.stack()[0][3], jamf_hostname.get()))
                tkMessageBox.showerror("Jamf login", "HTTP error from:\n%s" % jamf_hostname.get())
        except urllib2.URLError:
            logger.error("%s: Error contacting JSS: %s" % (inspect.stack()[0][3], jamf_hostname.get()))
            tkMessageBox.showerror("Jamf login", "Unable to contact:\n%s" % jamf_hostname.get())
        except Exception as exception_message:
            logger.error("%s: Generic error. (%r)" % (inspect.stack()[0][3], exception_message))
            tkMessageBox.showerror("Jamf login", "Generic error from %s." % jamf_hostname.get())

        sys.exit()

    #
    # This is really important. This list contains the required rights for the fields we need to access.
    read_privileges = ['Read Accounts', 'Read Buildings', 'Read Computers', 'Read Departments', 'Read User', 'Read LDAP Servers']
    update_privileges = ['Update Computers', 'Update User']

    # read or create prefs
    preference_file, preference_path = read_create_prefs(logger)
    hostnames = injest_prefs(logger, preference_file).split(',')

    if 'new_server' not in hostnames[0]:
        hostnames.append("https://new_server:8443")

    root = Tk()
    jamf_username = StringVar()
    jamf_password = StringVar()
    jamf_hostname = StringVar()

    #
    # build and display login screen
    root.title("Jamf Login")
    mainframe = ttk.Frame(root)
    mainframe.grid(column=0, row=0, sticky=NSEW)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.geometry('+0+0')

    ttk.Label(mainframe, text="Jamf Server:").grid(column=1, row=10, sticky=E)

    hostname_combobox = ttk.Combobox(mainframe, width=30, textvariable=jamf_hostname)
    hostname_combobox['values'] = hostnames
    hostname_combobox.current(0)
    hostname_combobox.grid(column=2, row=10, sticky=EW)

    ttk.Label(mainframe, text="Username:").grid(column=1, row=20, sticky=E)
    uname_entry = ttk.Entry(mainframe, width=30, textvariable=jamf_username)
    uname_entry.grid(column=2, row=20, sticky=EW)

    ttk.Label(mainframe, text="Password:").grid(column=1, row=30, sticky=E)
    pword_entry = ttk.Entry(mainframe, width=30, textvariable=jamf_password, show="*")
    pword_entry.grid(column=2, row=30, sticky=EW)

    if platform.system() == 'Darwin':
        ttk.Button(mainframe, text="Quit", command=sys.exit).grid(column=2, row=70, padx=3)
    else:
        ttk.Button(mainframe, text="Quit", command=sys.exit).grid(column=2, row=70, padx=3, sticky=W)

    ttk.Button(mainframe, text="Login", default='active', command=try_login).grid(column=2, row=70, padx=3, sticky=E)

    if platform.system() == 'Darwin':
        tmpl = 'tell application "System Events" to set frontmost of every process whose unix id is {} to true'
        script = tmpl.format(os.getpid())
        output = subprocess.check_call(['/usr/bin/osascript', '-e', script])

    root.bind('<Return>', lambda event: try_login())

    uname_entry.focus()
    root.mainloop()

    if preference_path:
        modify_prefs(logger, preference_file, preference_path, hostnames, jamf_hostname.get())
    else:
        logger.error("No path to preferences, no save attempt.")

    return (jamf_hostname.get(), jamf_username.get(), jamf_password.get(), access_level)


def main():
    """
    Cooridnates login and app launching
    """
    access_level = ''

    logger = loggers.file_logger(name='tugboat')
    logger.info("Running Tugboat")
    logger.info("Level: Method/function: Message")

    jamf_hostname, jamf_username, jamf_password, access_level = login(logger)
    if not jamf_username:
        sys.exit(0)

    root = Tk()
    my_app = Computer(root, logger, jamf_hostname, jamf_username, jamf_password, access_level)

    root.mainloop()

if __name__ == '__main__':
    main()
