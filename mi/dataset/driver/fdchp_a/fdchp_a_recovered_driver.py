#!/usr/bin/env python

"""
@package mi.dataset.driver.fdchp_a
@file mi/dataset/driver/fdchp_a/fdchp_a_recovered_driver.py
@author Emily Hahn
@brief Driver for the fdchp series a recovered instrument
"""

from mi.dataset.dataset_driver import SimpleDatasetDriver
from mi.dataset.parser.fdchp_a import FdchpAParser


def parse(basePythonCodePath, sourceFilePath, particleDataHdlrObj):
    """
    This is the method called by Uframe
    :param basePythonCodePath This is the file system location of mi-dataset
    :param sourceFilePath This is the full path and filename of the file to be parsed
    :param particleDataHdlrObj Java Object to consume the output of the parser
    :return particleDataHdlrObj
    """

    with open(sourceFilePath, 'rb') as stream_handle:

        # create and instance of the concrete driver class defined below
        driver = FdchpARecoveredDriver(basePythonCodePath, stream_handle, particleDataHdlrObj)
        driver.processFileStream()

    return particleDataHdlrObj


class FdchpARecoveredDriver(SimpleDatasetDriver):
    """
    Derived fdchp a driver class
    All this needs to do is create a concrete _build_parser method
    """
    def _build_parser(self, stream_handle):
        # build the parser
        return FdchpAParser(stream_handle, self._exception_callback)

