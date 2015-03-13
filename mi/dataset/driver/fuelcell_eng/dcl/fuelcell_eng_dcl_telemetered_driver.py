#!/usr/bin/env python

"""
@package mi.dataset.driver.fuelcell_eng.dcl
@file mi-dataset/mi/dataset/driver/fuelcell_eng/dcl/fuelcell_eng_dcl_telemetered_driver.py
@author Chris Goodrich
@brief Telemetered driver for the fuelcell_eng_dcl instrument

Release notes:

Initial Release
"""

from mi.dataset.dataset_driver import SimpleDatasetDriver
from mi.dataset.dataset_parser import DataSetDriverConfigKeys
from mi.dataset.parser.fuelcell_eng_dcl import FuelCellEngDclParticleClassKey,\
    FuelCellEngDclDataParticleTelemetered
from mi.dataset.parser.fuelcell_eng_dcl import FuelCellEngDclParser


def parse(basePythonCodePath, sourceFilePath, particleDataHdlrObj):
    """
    This is the method called by Uframe
    :param basePythonCodePath This is the file system location of mi-dataset
    :param sourceFilePath This is the full path and filename of the file to be parsed
    :param particleDataHdlrObj Java Object to consume the output of the parser
    :return particleDataHdlrObj
    """

    with open(sourceFilePath, 'rU') as stream_handle:

        # create and instance of the concrete driver class defined below
        driver = FuelCellEngDclRecoveredDriver(basePythonCodePath, stream_handle, particleDataHdlrObj)
        driver.processFileStream()

    return particleDataHdlrObj


class FuelCellEngDclRecoveredDriver(SimpleDatasetDriver):
    """
    The fuelcell_eng_dcl driver class extends the SimpleDatasetDriver.
    All this needs to do is create a concrete _build_parser method
    """

    def _build_parser(self, stream_handle):

        self.parser_config = {
            DataSetDriverConfigKeys.PARTICLE_MODULE: 'mi.dataset.parser.fuelcell_eng_dcl',
            DataSetDriverConfigKeys.PARTICLE_CLASS: None,
            DataSetDriverConfigKeys.PARTICLE_CLASSES_DICT: {
                FuelCellEngDclParticleClassKey.ENGINEERING_DATA_PARTICLE_CLASS: FuelCellEngDclDataParticleTelemetered
            }
        }

        parser = FuelCellEngDclParser(self.parser_config,
                                      stream_handle,
                                      self._exception_callback)

        return parser
