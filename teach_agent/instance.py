import os
from contextlib import contextmanager


@contextmanager
def instance_lock(root):
    file=(root/'service.lock').open('a+b')
    file.seek(0,2)
    if file.tell()==0:
        file.write(b'1');file.flush()
    file.seek(0)
    try:
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(file.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(file.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except OSError as error:
        file.close()
        raise RuntimeError('这个数据目录的工作台已在运行，请打开现有窗口') from error
    try:
        yield
    finally:
        file.seek(0)
        if os.name=='nt':
            msvcrt.locking(file.fileno(),msvcrt.LK_UNLCK,1)
        else:
            fcntl.flock(file.fileno(),fcntl.LOCK_UN)
        file.close()
