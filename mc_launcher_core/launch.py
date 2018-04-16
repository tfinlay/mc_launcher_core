"""
Thanks to code from: https://github.com/TechnicPack/MinecraftCore/blob/master/src/main/java/net/technicpack/minecraftcore/launch/MinecraftLauncher.java#L86
"""
import json
import logging
import os.path
import platform
import subprocess
import mc_launcher_core
from mc_launcher_core.javautils import version_at
from mc_launcher_core.exceptions import LibraryMissingError, MinecraftNotFoundError
from mc_launcher_core.util import get_required_libraries_paths, get_url_filename, get_minecraft_launch_details, java_esque_string_substitutor


logger = logging.getLogger(__name__)


def generate_class_path(bindir, libcache):
    """
    Generates the class path based off the contents of minecraft.json
    :param bindir: string
    :param libcache: string, path to place where all libraries are kept (shared across minecrafts)
    :return: string
    """
    logger.debug("Generating class path...")
    minecraft_path = os.path.join(bindir, "minecraft.jar")
    modloader_path = os.path.join(bindir, 'modloader.jar')

    cp = []

    # add Minecraft jar
    if not os.path.isfile(minecraft_path):
        raise MinecraftNotFoundError(minecraft_path)

    cp.append(minecraft_path)

    # add the modloader
    logger.debug("Checking if modloader.jar exists...")
    if os.path.isfile(modloader_path):
        # add this
        logger.debug("modloader.jar exists! adding to cp")
        cp.append(modloader_path)
    else:
        logger.warning("Failed to find modloader.jar, if this launch supposed to be Vanilla?")

    for lib in get_required_libraries_paths(bindir):
        logger.debug("Processing library at path: {}".format(lib))
        filepath = os.path.join(libcache, *lib.split("/"))

        if not os.path.isfile(filepath):
            raise LibraryMissingError(filepath, "Required Library at path: '{}' wasn't found".format(filepath))

        cp.append(filepath)

    logger.debug("done!")

    return os.path.pathsep.join(cp)  # type: str


def build_commands(bindir, gamedir, assetsdir, javapath, session, memory, libcache):
    # type: (str, str, str, str, mc_launcher_core.MinecraftSession, int, str) -> list
    """
    :param bindir: string, absolute path to the bin directory containing minecraft.jar, modloader.jar (if any), minecraft.json, and natives/
    :param gamedir: string, absolute path to game directory
    :param assetsdir: string, absolute path to the assets directory (this can be shared across Minecraft versions)
    :param javapath string, absolute path to Java executable
    :param session: MinecraftSession, the current session
    :param memory: int, amount of memory to dedicate to this launch (in megabytes)
    :param libcache: string, path to place where all libraries are kept (shared across minecrafts)
    :return:
    """
    logger.info("Building launch commands...")
    j = version_at(javapath)
    commands = list()

    commands.append(javapath)

    if platform.system() == "Windows":
        commands.append("-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump")
    elif platform.system() == "Darwin":
        #commands.append("-Xdock:icon")
        raise NotImplementedError("MacOS Build commands aren't quite ready yet")

    # Java 1.8 fix, see technic code page
    perm_size = 128
    if memory >= (1024*6):
        perm_size = 512
    elif memory >= 2048:
        perm_size = 256

    commands.append("-Xms{}m".format(memory))
    commands.append("-Xmx{}m".format(memory))

    #if j.version_is_atleast("1.8"):
    #    commands.append("-XX:MaxPermSize={}m".format(perm_size))

    if memory >= 4096:
        if j.version_is_atleast("1.7"):
            commands.append("-XX:+UseG1GC")
            commands.append("-XX:MaxGCPauseMillis=4")
        else:
            commands.append("-XX:+UseConcMarkSweepGC")

    commands.append("-Djava.library.path={}".format(os.path.join(bindir, "natives")))

    commands.append("-Dminecraft.applet.TargetDirectory={}".format(os.path.abspath(gamedir)))
    commands.append("-Djava.net.preferIPv4Stack=true")

    commands.append("-cp")
    commands.append(generate_class_path(bindir, libcache))

    launch_details = get_minecraft_launch_details(bindir)

    commands.append(launch_details["classpath"])

    minecraft_args = dict(
        auth_player_name=session.selected_user.display_name,
        auth_uuid=session.selected_user.id,

        auth_username=session.username,
        auth_session=session.get_session_id(),
        auth_access_token=session.access_token,
        accessToken=session.access_token,

        version_name=launch_details["version_id"],
        game_directory=gamedir,
        assets_root=assetsdir,
        game_assets=assetsdir,
        user_type='legacy' if session.selected_user.legacy else 'mojang',
        user_properties='{}',
        assets_index_name=launch_details["version_id"],

        version=launch_details["version_id"],
        version_type=launch_details["version_type"]
    )

    logger.debug("filling launch details into: '{}' from: {}".format(launch_details["args"], minecraft_args))

    for item in launch_details["args"].split(" "):
        commands.append(java_esque_string_substitutor(item, **minecraft_args))

    #commands.append(java_esque_string_substitutor(launch_details["args"], **minecraft_args))

    return commands
