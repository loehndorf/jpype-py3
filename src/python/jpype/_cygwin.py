#*****************************************************************************
#   Copyright 2013 Thomas Calmant
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#*****************************************************************************

from . import _jvmfinder
import os
import subprocess

# ------------------------------------------------------------------------------

def cygwin_to_windows(cygwin_path):
    """
    Uses ``cygpath`` to convert a Cygwin path to a Windows path

    :param cygwin_path: The Cygwin path to convert
    :return: The corresponding Windows path
    """
    process = subprocess.Popen(['cygpath', '-w', cygwin_path],
                               stdout=subprocess.PIPE)
    return str(process.stdout.readline(), 'UTF-8').strip()

# ------------------------------------------------------------------------------


class CygwinJVMFinder(_jvmfinder.JVMFinder):
    """
    Cygwin JVM library finder class
    """
    def __init__(self):
        """
        Sets up members
        """
        # Call the parent constructor
        _jvmfinder.JVMFinder.__init__(self)

        # Library file name
        self._libfile = "jvm.dll"

        # Predefined locations
        self._locations = set()
        for key in (
                # 64 bits (or 32 bits on 32 bits OS) JDK
                'ProgramFiles'
                # 32 bits JDK on 32 bits OS
                'ProgramFiles(x86)'):
            try:
                env_folder = os.environ[key]
                self._locations.add(os.path.join(env_folder, "Java"),)
            except KeyError:
                # Environment variable is missing (ignore)
                pass

        # Search methods
        self._methods = (self._get_from_java_home,
                         self._get_from_known_locations)

    def get_boot_arguments(self, jvm_lib_path):
        """
        Prepares the arguments required to start a JVM in Cygwin.

        :param jvm_lib_path: Path to the jvm.dll file, Cygwin style
        :return: The list of arguments to add for the JVM to start
        :raise OSError: Can't find required files
        """
        parts = jvm_lib_path.lower().split(os.sep)
        for idx, part in enumerate(reversed(parts)):
            if 'jre' in part or 'jdk' in part:
                break
        else:
            raise OSError("Can't find the root jre nor jdk folder.")

        # Compute the root folder
        java_home = os.path.sep.join([] + parts[:-idx])

        # Look for zip.dll and rt.jar
        library_path = None
        boot_classpath = None
        for root, _, filenames in os.walk(java_home):
            if "zip.dll" in filenames:
                # Found the library folder, store the folder Windows path
                library_path = cygwin_to_windows(root)
                if boot_classpath is not None:
                    break
            elif "rt.jar" in filenames:
                # Found the core JAR file, store the whole Windows path
                boot_classpath = cygwin_to_windows(os.path.join(root, "rt.jar"))
                if library_path is not None:
                    break
        else:
            raise OSError("A folder has not been found: library path='{0}' -- "
                          "boot path='{1}'"
                          .format(library_path, boot_classpath))

        # Return the result as JVM properties
        return ['-Dsun.boot.library.path={0}'.format(library_path),
                '-Xbootclasspath:{0}'.format(boot_classpath)]