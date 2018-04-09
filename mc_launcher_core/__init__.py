"""
In charge of the base low-level Minecraft API stuff
"""
import logging
import subprocess
from mc_launcher_core.web import authenticate_user
from mc_launcher_core.launch import build_commands
logger = logging.getLogger(__name__)


class MinecraftUserProfile:
    """
    A Minecraft User Profile, based on data from Authentication's response
    """
    def __init__(self, id, name, legacy=False):
        self.id = id
        self.display_name = name
        self.legacy = legacy


def make_minecraft_user_profile(d):
    """
    Constructs a MinecraftUserProfile from authentication response raw data
    :param d: dict<id: string, name: string, id: bool>
    :return: MinecraftUserProfile
    """
    try:
        legacy = d["legacy"]
    except KeyError:
        legacy = False

    return MinecraftUserProfile(d["id"], d["name"], legacy)


class MinecraftSession:
    """
    A 'session' of Minecraft, basically loads login information and preps for launching minecraft
    THE PASSWORD IS NOT STORED. Store the client_token for persistence instead.
    """
    def __init__(self, username, password, client_token=None):
        self.username = username
        self.available_users = []

        self._authenticate(password, client_token)

    def _authenticate(self, password, client_token):
        """
        Makes an auth request and processes what is received
        :param password: string, the user's password
        :param client_token: string / None
        :return: None
        """
        res = authenticate_user(self.username, password, True, client_token)

        if client_token is not None:
            self.client_token = client_token
        else:
            self.client_token = res["clientToken"]

        self.access_token = res["accessToken"]

        self.selected_user = make_minecraft_user_profile(res["selectedProfile"])
        self.user_id = res["user"]["id"]

        for user in res["availableProfiles"]:
            self.available_users.append(make_minecraft_user_profile(user))

    def get_session_id(self):
        return "token:{}:{}".format(self.access_token, self.selected_user.id)

    def select_user(self):
        raise NotImplementedError()

    def launch(self, bindir, gamedir, assetsdir, javapath, memory, libcache):
        """
        Launch Minecraft
        :param bindir: string, absolute path to the bin directory containing minecraft.jar, modloader.jar (if any), minecraft.json, and natives/
        :param gamedir: string, absolute path to game directory
        :param assetsdir: string, absolute path to the assets directory (this can be shared across Minecraft versions)
        :param javapath: string, absolute path to Java executable
        :return: None (atm) TODO: return stream of Minecraft output
        """
        from pprint import pprint as pp
        commands = build_commands(
            bindir=bindir,
            gamedir=gamedir,
            assetsdir=assetsdir,
            javapath=javapath,
            session=self,
            memory=memory,
            libcache=libcache
        )

        print(commands)

        proc = subprocess.Popen(commands, shell=True)
        proc.communicate()


if __name__ == "__main__":
    session = MinecraftSession("")