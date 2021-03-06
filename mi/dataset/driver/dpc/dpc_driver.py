#!/usr/local/bin/python2.7
##
# OOIPLACEHOLDER
#
# Copyright 2014 Raytheon Co.
##
from mi.dataset.dataset_driver import DataSetDriver

from mi.dataset.parser.dpc import DeepProfilerParser
from mi.core.log import get_logger
from mi.logging import config
import os

log = get_logger()

def parse(basePythonCodePath, sourceFilePath, particleDataHdlrObj):
    config.add_configuration(os.path.join(basePythonCodePath, 'res', 'config', 'mi-logging.yml'))
    with open(sourceFilePath, "r") as stream_handle:

        def exception_callback(exception):
                log.debug("Exception: %s", exception)
                particleDataHdlrObj.setParticleDataCaptureFailure()

        parser = DeepProfilerParser({}, stream_handle, exception_callback)
        driver = DataSetDriver(parser, particleDataHdlrObj)
        driver.processFileStream()

    return particleDataHdlrObj