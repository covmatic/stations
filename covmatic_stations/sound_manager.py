import logging
import subprocess


class SoundManager:
    def __init__(self,
                 player_command: str = "mpg123",
                 argument_format: str = "{}",  # '{}' will be replaced with filename
                 **kwargs):
        self._logger = logging.getLogger(__name__)
        self._player_command = player_command
        self._argument_format = argument_format
        self._filenames = kwargs
        self._logger.debug("Passed kwargs: {}".format(kwargs))
        self._process = None

    def _get_argument(self, filename) -> str:
        return self._argument_format.format(filename)

    def play(self, sound: str):
        self._logger.debug("Playing {}".format(sound))
        self.kill()
        try:
            if sound in self._filenames:
                argument = self._get_argument(self._filenames[sound])
                self._logger.debug("Command is: {}; argument is: {}".format(self._player_command, argument))
                self._process = subprocess.Popen([self._player_command, argument],
                                                 stdin=subprocess.DEVNULL,
                                                 stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL)
            else:
                self._logger.error("Sound {} not found".format(sound))
        except Exception as e:
            self._logger.error("Error playing sound {}: {}".format(sound, e))

    def cleanup(self, timeout=15):
        if self._process and self._process.poll() is None:
            try:
                self._logger.debug("Waiting for sound to finish")
                self._process.wait(timeout)
                self._process.communicate()
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.communicate()

    def kill(self):
        if self._process and self._process.poll() is None:
            try:
                self._logger.debug("Killing process")
                self._process.kill()
                self._process.communicate()
            except Exception as e:
                self._logger.error("Exception during kill: {}".format(e))
        else:
            self._logger.debug("Process is None or finished")

# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
