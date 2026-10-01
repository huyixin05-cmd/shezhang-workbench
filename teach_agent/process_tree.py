"""Own subprocess descendants even when their original parent exits."""
import os
import signal
import subprocess


class ProcessTree:
    def __init__(self, command, **kwargs):
        self.job = None
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
            self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
            self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
            self.kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
            self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            class Basic(ctypes.Structure):
                _fields_=[('process_time',ctypes.c_int64),('job_time',ctypes.c_int64),('flags',wintypes.DWORD),
                    ('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active',wintypes.DWORD),
                    ('affinity',ctypes.c_size_t),('priority',wintypes.DWORD),('scheduling',wintypes.DWORD)]
            class Extended(ctypes.Structure):
                _fields_=[('basic',Basic),('io',ctypes.c_uint64*6),('memory',ctypes.c_size_t*4)]
            self.kernel.SetInformationJobObject.argtypes=[wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD]
            self.job = self.kernel.CreateJobObjectW(None, None)
            if not self.job: raise ctypes.WinError(ctypes.get_last_error())
            limits=Extended();limits.basic.flags=0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not self.kernel.SetInformationJobObject(self.job,9,ctypes.byref(limits),ctypes.sizeof(limits)):
                self.kernel.CloseHandle(self.job);self.job=None
                raise ctypes.WinError(ctypes.get_last_error())
        else:
            kwargs['start_new_session'] = True
        try:
            self.process = subprocess.Popen(command, **kwargs)
            if self.job and not self.kernel.AssignProcessToJobObject(self.job, int(self.process._handle)):
                error = ctypes.WinError(ctypes.get_last_error())
                self.process.kill(); self.process.wait()
                raise error
        except BaseException:
            if self.job: self.kernel.CloseHandle(self.job); self.job = None
            raise

    def close(self):
        if self.job:
            self.kernel.TerminateJobObject(self.job, 1)
            self.kernel.CloseHandle(self.job); self.job = None
        elif os.name != 'nt':
            try: os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
        if self.process.poll() is None: self.process.kill()
        self.process.wait(timeout=10)

    def __enter__(self): return self.process
    def __exit__(self, *exc): self.close()
