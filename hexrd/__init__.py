# ============================================================
# Copyright (c) 2012, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
# Written by Joel Bernier <bernier2@llnl.gov> and others.
# LLNL-CODE-529294.
# All rights reserved.
#
# This file is part of HEXRD. For details on dowloading the source,
# see the file COPYING.
#
# Please also see the file LICENSE.
#
# This program is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License (as published by the Free Software
# Foundation) version 2.1 dated February 1999.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the IMPLIED WARRANTY OF MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the terms and conditions of the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program (see file LICENSE); if not, write to
# the Free Software Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA 02111-1307 USA or visit <http://www.gnu.org/licenses/>.
# ============================================================

from __future__ import print_function

import logging

# Release data
__author__ = 'HEXRD Development Team <praxes@googlegroups.com>'
__license__ = 'LGPLv2'

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

def _readenv(name, ctor, default):
    try:
        import os
        res = os.environ[name]
        del os
    except KeyError:
        del os
        return default
    else:
        try:
            return ctor(res)
        except:
            import warnings
            warnings.warn("environ %s defined but failed to parse '%s'" %
                          (name, res), RuntimeWarning)
            del warnings
            return default


# 0 = do NOT use numba
# 1 = use numba (default)
USE_NUMBA = _readenv("HEXRD_USE_NUMBA", int, 1)
if USE_NUMBA:
    try:
        import numba
    except ImportError:
        print("*** Numba not available, processing may run slower ***")
        USE_NUMBA = False

del _readenv


#doc_url = 'latest' if 'dev' in __version__ else 'v%s' % __version__
doc_url = 'latest'
doc_url = 'http://hexrd.readthedocs.org/en/%s' % doc_url



try:
    from IPython import embed as debug
except ImportError:
    pass
