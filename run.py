import os
import pickle
from mc_launcher_core import MinecraftSession

if os.path.isfile("savedsess.pickle"):
    with open("savedsess.pickle", 'rb') as f:
        sess = pickle.load(f)
else:
    sess = MinecraftSession("tefinlay2011@hotmail.com", "UltraSecure1", "5b9abb8c363a49dcb365fc8a31955ba1")

print(sess.client_token)

bindir = r"C:\Users\Thomas Finlay\AppData\Roaming\.technic\modpacks\the-stefan-pack - Copy\bin"
gamedir = r"C:\Users\Thomas Finlay\AppData\Roaming\.technic\modpacks\test"
assetsdir = r"C:\Users\Thomas Finlay\AppData\Roaming\.technic\assets"
javapath = r"C:\ProgramData\Oracle\Java\javapath\java.exe"
memory = 2048
libcache = r"C:\Users\Thomas Finlay\AppData\Roaming\.technic\cache"

with open("savedsess.pickle", 'wb') as f:
    pickle.dump(sess, f)

sess.launch(bindir, gamedir, assetsdir, javapath, memory, libcache)
