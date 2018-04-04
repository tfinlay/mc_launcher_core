"""
Java utilities
"""


class JavaVersion:
    def __init__(self, version):
        self.version = version

    def version_is_atleast(self, v):
        for this, that in zip(self.version.split('.'), v.split('.')):
            if int(this) > int(that):
                return True

        return False


def version_at(path):
    """
    Gets the Java version installed at path
    :param path: string
    :return: JavaVersion
    """