import os

command = (
    'powershell.exe -NoExit -Command "wsl.exe qemu-system-i386 '
    '-fda \'/mnt/d/remote_osfinal-main/os_files/os-image.bin\' '
    '-display curses"'
)

os.system(command)
