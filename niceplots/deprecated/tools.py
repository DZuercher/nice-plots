import os
import platform
import subprocess


def is_tool(name):
    try:
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            return False
    return True


def find_prog(prog):
    if is_tool(prog):
        cmd = "where" if platform.system() == "Windows" else "which"

        p = subprocess.Popen(
            [cmd, prog],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        output, err = p.communicate()
        return output.decode("utf-8").rstrip()
