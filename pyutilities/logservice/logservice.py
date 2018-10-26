# --coding:utf-8--
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

# -----------------------------
# Copyright by Intel
# -----------------------------

import sys
import logging

try:
    from logging import RotatingFileHandler
except BaseException:
    from logging.handlers import RotatingFileHandler


class LogService(object):
    @classmethod
    def initialize(
            cls,
            output='console',
            level_str='debug',
            fp=None,
            maxsize=10485760):
        logger = logging.getLogger()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        level = LogService._nameToLevel(level_str.upper())
        logger.setLevel(level)
        logger.addHandler(logging.NullHandler())

        if output in ['file', 'all']:
            f_path = fp
            try:
                f_maxsize = int(maxsize)
            except BaseException:
                f_maxsize = 10485760
            file_hanlder = RotatingFileHandler(f_path, maxBytes=f_maxsize)
            file_hanlder.setFormatter(formatter)
            logger.addHandler(file_hanlder)

        if output in ['console', 'all']:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    @classmethod
    def getLogger(cls, name):
        return logging.getLogger(name)

    @classmethod
    def _nameToLevel(cls, level_str):
        if sys.version_info.major == 3:
            return logging._nameToLevel.get(level_str.upper())
        else:
            return logging._levelNames.get(level_str.upper())
