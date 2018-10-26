# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import symtable
import os
import sys

sys.path.append("../../../pyutilities")
from logservice.logservice import LogService
logger = LogService.getLogger(__name__)

SOURCE = "./udf/udf_simple.py"

IMPORTS_WHITELIST = ['json']
# builtin functions blacklist, should remove all system builtins and use
# whitelist in the future
BUILTIN_FUNC_BLACKLIST = [
    'eval',
    'exec',
    'dir',
    'globals',
    'setattr',
    'delattr',
    'hasattr',
    '__import__']

PROCESS_FUNC_NAME = 'process'


def _check_process_func(sym):

    ns = sym.get_namespace()

    if ns.get_type() != 'function':
        logger.error("'process' defined is not a function!")
        return False

    # check if parameter number equals 1
    if len(ns.get_parameters()) != 1:
        logger.error("Only 1 parameter is allowed for process function!")
        return False

    # check symbols in process function
    for sym in ns.get_symbols():
        if sym.is_namespace() or sym.is_imported():
            logger.error(
                "Embedding import, function and class is are not allowed in process function: '{}'!".format(
                    sym.get_name()))
            return False

        if not _check_builtin_functions(sym):
            return False

    return True


def _check_builtin_functions(sym):
    if sym.get_name() in BUILTIN_FUNC_BLACKLIST:
        logger.error("'{}' function is not allowed!".format(sym.get_name()))
        return False
    return True


def _check_imports(sym):
    if sym.get_name() not in IMPORTS_WHITELIST:
        logger.error("Module imports not allowed: {}".format(sym.get_name()))
        return False
    return True


def check_existance(source_file_path):
    return os.path.exists(source_file_path)


def validate_udf_file(source_file):
    with open(source_file) as file:
        try:
            # will raise exception if not pass python compiler syntax and
            # semantic check
            symbols = symtable.symtable(
                code=file.read(),
                filename=SOURCE,
                compile_type='exec')

            # check 'process' function
            try:
                sym_process = symbols.lookup(PROCESS_FUNC_NAME)
            except BaseException:
                logger.error(
                    "Can't find UDF function named 'process', the UDF file is not valid!")
                return False

            if not _check_process_func(sym_process):
                return False

            #  run through top namespace
            for sym in symbols.get_symbols():
                # checking imports
                if sym.is_imported():
                    if not _check_imports(sym):
                        return False
                # checking eval function
                if not _check_builtin_functions(sym):
                    return False
                # checking functions and classes
                if sym.is_namespace() and sym.get_name() != PROCESS_FUNC_NAME:
                    logger.error(
                        "Can't define functions or classes other than 'process': {}".format(
                            sym.get_name()))
                    return False

            return True

        except Exception as e:
            logger.error('Loading UDF file error: ' + str(e))
            return False


if __name__ == "__main__":
    print("UDF Source file is: " + SOURCE)
    print("Checking if UDF is valid: " + str(validate_udf_file(SOURCE)))
