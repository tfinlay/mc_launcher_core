"""
Thanks to code from: https://github.com/TechnicPack/MinecraftCore/blob/master/src/main/java/net/technicpack/minecraftcore/launch/MinecraftLauncher.java#L86
"""
import subprocess
import os.path
import platform
from mc_launcher_core.javautils import version_at


def build_commands(bindir, gamedir, assetsdir, javapath, user, memory):
    """
    :param bindir: string, absolute path to the bin directory containing minecraft.jar, modloader.jar (if any), minecraft.json, and natives/
    :param gamedir: string, absolute path to game directory
    :param assetsdir: string, absolute path to the assets directory (this can be shared across Minecraft versions)
    :param javapath string, absolute path to Java executable
    :param user: MinecraftUserProfile
    :param memory: int, amount of memory to dedicate to this launch (in megabytes)
    :return:
    """
    j = version_at(javapath)
    commands = []

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

    if j.version_is_atleast("1.8"):
        commands.append("-XX:MaxPermSize={}m".format(perm_size))

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
    commands.append()
