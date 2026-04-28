import ctypes
from ctypes import wintypes
import psutil
from typing import TypedDict

user32 = ctypes.windll.user32
shcore = ctypes.windll.shcore
kernel32 = ctypes.windll.kernel32

TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class RECT(ctypes.Structure):
    left: int
    top: int
    right: int
    bottom: int

    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG)
    ]


class MONITORINFOEX(ctypes.Structure):
    cbSize: int
    rcMonitor: RECT
    rcWork: RECT
    dwFlags: int
    szDevice: str

    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32)
    ]


class PROCESSENTRY32W(ctypes.Structure):
    dwSize: int
    cntUsage: int
    th32ProcessID: int
    th32DefaultHeapID: int
    th32ModuleID: int
    cntThreads: int
    th32ParentProcessID: int
    pcPriClassBase: int
    dwFlags: int
    szExeFile: str

    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260)
    ]


class MonitorInfo(TypedDict):
    monitor_name: str
    exe_name: str
    actual_width: int
    actual_height: int
    scale_percent: int
    scale_factor: float


def set_dpi_awareness():
    try:
        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
        user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        return
    except Exception:
        pass

    try:
        shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass

    try:
        user32.SetProcessDPIAware()
        return
    except Exception:
        raise RuntimeError("无法获取屏幕DPI")


def get_pids_by_psutil(exe_name: str) -> set:
    exe_name = exe_name.lower()
    pids = []
    for p in psutil.process_iter(["pid", "name"]):
        name = (str(p.info.get("name", ""))).lower()
        if name == exe_name:
            pids.append(p.info["pid"])
    return set(pids)


def get_pids_by_name(exe_name: str) -> set:
    exe_name = exe_name.lower()
    pids = []

    hSnap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if hSnap == INVALID_HANDLE_VALUE:
        return get_pids_by_psutil(exe_name)

    pe = PROCESSENTRY32W()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    ok = kernel32.Process32FirstW(hSnap, ctypes.byref(pe))
    while ok:
        if pe.szExeFile.lower() == exe_name:
            pids.append(pe.th32ProcessID)
        ok = kernel32.Process32NextW(hSnap, ctypes.byref(pe))
    kernel32.CloseHandle(hSnap)
    return set(pids)


def get_main_window_by_pids(pids: set) -> wintypes.HWND | None:
    ret = None

    def callback(hwnd: wintypes.HWND, lparam):
        nonlocal ret
        if not user32.IsWindowVisible(hwnd):
            return True

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids:
            ret = hwnd
            return False
        return True

    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return ret


def get_monitor_info_from_window(hwnd: wintypes.HWND) -> MONITORINFOEX | None:
    MONITOR_DEFAULTTONEAREST = 2
    hmon = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    if not hmon:
        return None

    mon_info = MONITORINFOEX()
    mon_info.cbSize = ctypes.sizeof(MONITORINFOEX)
    if not user32.GetMonitorInfoW(hmon, ctypes.byref(mon_info)):
        return None

    return mon_info


def get_scale_factor(hmon: MONITORINFOEX) -> int | None:
    try:
        scale = wintypes.DWORD()
        result = shcore.GetScaleFactorForMonitor(hmon, ctypes.byref(scale))
        if result == 0:
            return scale.value
    except Exception:
        pass

    try:
        MDT_EFFECTIVE_DPI = 0
        dpi_x = wintypes.UINT()
        dpi_y = wintypes.UINT()
        result = shcore.GetDpiForMonitor(
            hmon, MDT_EFFECTIVE_DPI, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
        if result == 0:
            return round(dpi_x.value / 96.0 * 100)
    except Exception:
        pass

    return None


def get_process_monitor_info(exe_name: str) -> MonitorInfo | None:
    pids = get_pids_by_name(exe_name)
    if not pids:
        return None

    hwnd = get_main_window_by_pids(pids)
    if not hwnd:
        return None

    mon_info = get_monitor_info_from_window(hwnd)
    if not mon_info:
        return None

    scale = get_scale_factor(mon_info)
    if not scale:
        return None

    actual_width = mon_info.rcMonitor.right - mon_info.rcMonitor.left
    actual_height = mon_info.rcMonitor.bottom - mon_info.rcMonitor.top

    return MonitorInfo(monitor_name=mon_info.szDevice, exe_name=exe_name, actual_width=actual_width, actual_height=actual_height, scale_percent=scale, scale_factor=scale/100)

# usage
# set_dpi_awareness()
# get_process_monitor_info(exe_name)

