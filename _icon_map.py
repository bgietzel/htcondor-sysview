#!/usr/bin/env python
#
# $Id: Exp $
#
# Icon mapping for groups and users

import re, string

def find_dot_type(accounting_group=None, Owner=None, Group=None, group=None, dUser=None):

    dot_type = ''

    if Owner.startswith('test') and accounting_group.startswith('group_test'):
        dot_type = 'x'
    elif Group.startswith("TEST1"):
        dot_type = 'A'
    elif Group.startswith("somegroup"):
        dot_type = 'C'
    elif accounting_group.startswith('physics') or accounting_group.startswith('CS'):
        dot_type = 'o'
      
    # find remote jobs from external domains
    if (dUser.find("remotedomain.org") >= 0):
        dot_type = 'O'
 
    return dot_type; 
