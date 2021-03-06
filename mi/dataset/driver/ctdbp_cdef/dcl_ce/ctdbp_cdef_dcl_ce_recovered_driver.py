#!/usr/bin/env python

"""
@package mi.dataset.driver.ctdbp_cdef.dcl_ce.ctdbp_cdef_dcl_ce
@file mi-dataset/mi/dataset/driver/ctdbp_cdef/dcl_ce/ctdbp_cdef_dcl_ce.py
@author Tapana Gupta
@brief Driver for the ctdbp_cdef_dcl_ce instrument

Release notes:

Initial Release
"""

from mi.dataset.dataset_parser import DataSetDriverConfigKeys
from mi.dataset.dataset_driver import SimpleDatasetDriver
from mi.dataset.parser.ctdbp_cdef_dcl_ce import \
    CtdbpCdefDclCeRecoveredParserDataParticle, \
    CtdbpCdefDclCeRecoveredParserDostaParticle, \
    PARTICLE_CLASS_KEY, \
    DOSTA_CLASS_KEY, \
    CtdbpCdefDclCeParser


def parse(basePythonCodePath, sourceFilePath, particleDataHdlrObj):
    """
    This is the method called by Uframe
    :param basePythonCodePath This is the file system location of mi-dataset
    :param sourceFilePath This is the full path and filename of the file to be parsed
    :param particleDataHdlrObj Java Object to consume the output of the parser
    :return particleDataHdlrObj
    """

    with open(sourceFilePath, 'rb') as stream_handle:

        # create an instance of the concrete driver class defined below
        driver = CtdbpCdefDclCeRecoveredDriver(basePythonCodePath, stream_handle, particleDataHdlrObj)
        driver.processFileStream()

    return particleDataHdlrObj


class CtdbpCdefDclCeRecoveredDriver(SimpleDatasetDriver):
    """
    Derived ctdbp_cdef_dcl_ce driver class
    All this needs to do is create a concrete _build_parser method
    """

    def _build_parser(self, stream_handle):

        parser_config = {
            DataSetDriverConfigKeys.PARTICLE_MODULE: 'mi.dataset.parser.ctdbp_cdef_dcl_ce',
            DataSetDriverConfigKeys.PARTICLE_CLASS: None,
            DataSetDriverConfigKeys.PARTICLE_CLASSES_DICT: {
                PARTICLE_CLASS_KEY: CtdbpCdefDclCeRecoveredParserDataParticle,
                DOSTA_CLASS_KEY: CtdbpCdefDclCeRecoveredParserDostaParticle,
            }
        }

        # The parser inherits from simple parser - other callbacks not needed here
        parser = CtdbpCdefDclCeParser(parser_config,
                                      stream_handle,
                                      self._exception_callback)

        return parser