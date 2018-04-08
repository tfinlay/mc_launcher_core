class InvalidLoginError(Exception):
    """
    The login details provided are invalid
    """


class LibraryMissingError(Exception):
    """
    When a required library isn't found
    """
    def __init__(self, libname, lib_data, *args):
        self.libname = libname
        self.lib_data = lib_data

        super().__init__(*args)


class MinecraftNotFoundError(Exception):
    """
    when Minecraft.jar isn't found at bindir/minecraft.jar
    """
    def __init__(self, checked_path, *args):
        self.checked_path = checked_path
        super().__init__(*args)


class InvalidMinecraftVersionError(Exception):
    """
    When the specified Minecraft version doesn't exist / couldn't be found
    """
    def __init__(self, version, *args):
        self.version = version
        super().__init__(*args)
