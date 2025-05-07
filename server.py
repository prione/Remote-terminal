import os
import time
import msvcrt
import ctypes
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32

# 定数定義
PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE = 0x00020016

class COORD(ctypes.Structure):
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

HPCON = wintypes.HANDLE

# STARTUPINFOEXW定義
class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]

class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [
        ("StartupInfo", STARTUPINFOW),
        ("lpAttributeList", wintypes.LPVOID)
    ]

# 関数宣言
CreatePseudoConsole = kernel32.CreatePseudoConsole
CreatePseudoConsole.argtypes = [COORD, wintypes.HANDLE, wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(HPCON)]
CreatePseudoConsole.restype = wintypes.HRESULT

InitializeProcThreadAttributeList = kernel32.InitializeProcThreadAttributeList
InitializeProcThreadAttributeList.argtypes = [wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.c_size_t)]
InitializeProcThreadAttributeList.restype = wintypes.BOOL

UpdateProcThreadAttribute = kernel32.UpdateProcThreadAttribute
UpdateProcThreadAttribute.argtypes = [wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD,
                                      wintypes.LPVOID, ctypes.c_size_t, wintypes.LPVOID, wintypes.LPVOID]
UpdateProcThreadAttribute.restype = wintypes.BOOL

DeleteProcThreadAttributeList = kernel32.DeleteProcThreadAttributeList
DeleteProcThreadAttributeList.argtypes = [wintypes.LPVOID]
DeleteProcThreadAttributeList.restype = None

CreateProcessW = kernel32.CreateProcessW

def create_conpty():
    hPC = HPCON()
    size = COORD(80, 25)

    hInRead, hInWrite = wintypes.HANDLE(), wintypes.HANDLE()
    hOutRead, hOutWrite = wintypes.HANDLE(), wintypes.HANDLE()
    kernel32.CreatePipe(ctypes.byref(hInRead), ctypes.byref(hInWrite), None, 0)
    kernel32.CreatePipe(ctypes.byref(hOutRead), ctypes.byref(hOutWrite), None, 0)

    result = CreatePseudoConsole(size, hInRead, hOutWrite, 0, ctypes.byref(hPC))
    if ctypes.get_last_error() != 0:
        raise ctypes.WinError(ctypes.get_last_error())

    return hPC, hInWrite, hOutRead

def spawn_cmd(hPC):
    size = ctypes.c_size_t()
    InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(size))
    attr_list = ctypes.create_string_buffer(size.value)
    InitializeProcThreadAttributeList(attr_list, 1, 0, ctypes.byref(size))
    UpdateProcThreadAttribute(attr_list, 0, PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE,
                              ctypes.byref(hPC), ctypes.sizeof(hPC), None, None)

    si = STARTUPINFOEXW()
    si.StartupInfo.cb = ctypes.sizeof(si)
    si.lpAttributeList = ctypes.cast(attr_list, wintypes.LPVOID)

    pi = (wintypes.HANDLE * 2)()
    success = CreateProcessW(None, "cmd.exe", None, None, False,
                             0x00080000 | 0x00000004, None, None,
                             ctypes.byref(si), ctypes.byref(pi))
    if not success:
        raise ctypes.WinError()

def main():
    hPC, hInWrite, hOutRead = create_conpty()
    spawn_cmd(hPC)

    while True:
        if os.path.exists("input.txt"):
            with open("input.txt", "r", encoding="utf-8") as f:
                cmd = f.read().strip() + "\n"
            os.remove("input.txt")
            msvcrt.write(hInWrite, cmd.encode("utf-8"))

            time.sleep(0.5)
            output = b""
            while kernel32.PeekNamedPipe(hOutRead, None, 0, None, None, None):
                buffer = ctypes.create_string_buffer(4096)
                bytesRead = wintypes.DWORD()
                success = kernel32.ReadFile(hOutRead, buffer, 4096, ctypes.byref(bytesRead), None)
                if not success or bytesRead.value == 0:
                    break
                output += buffer.raw[:bytesRead.value]

            with open("output.txt", "wb") as f:
                f.write(output + b"\n---END---\n")

        time.sleep(0.1)

if __name__ == "__main__":
    main()
