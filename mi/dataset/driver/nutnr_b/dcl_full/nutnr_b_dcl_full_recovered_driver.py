#!/usr/local/bin/python2.7
##
# OOIPLACEHOLDER
#
# Copyright 2014 Raytheon Co.
##
__author__ = 'mworden'

import os

from mi.logging import config
from mi.core.log import get_logger
from mi.dataset.dataset_parser import DataSetDriverConfigKeys
from mi.dataset.dataset_driver import DataSetDriver
from mi.dataset.parser.nutnr_b_dcl_full import NutnrBDclFullRecoveredParser

def parse(basePythonCodePath, sourceFilePath, particleDataHdlrObj):
    
    config.add_configuration(os.path.join(basePythonCodePath, 'res', 'config', 'mi-logging.yml'))

    log = get_logger()
    
    parser_config = {
        DataSetDriverConfigKeys.PARTICLE_MODULE: 'mi.dataset.parser.nutnr_b_particles',
        DataSetDriverConfigKeys.PARTICLE_CLASS: None
    }

    def exception_callback(exception):
        log.debug("ERROR: %r", exception)
        particleDataHdlrObj.setParticleDataCaptureFailure()
    
    with open(sourceFilePath, 'r') as stream_handle:
        parser = NutnrBDclFullRecoveredParser(parser_config,
                                              stream_handle,
                                              lambda state, ingested: None,
                                              lambda data : None,
                                              exception_callback)
        
        driver = DataSetDriver(parser, particleDataHdlrObj)
        driver.processFileStream()    

        
    return particleDataHdlrObj
