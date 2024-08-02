import os
import sqlite3
import time
from inotify_simple import INotify, flags

DATABASE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tracked_files.db')
TABLE_NAME = 'tracked_files'

def get_files_to_monitor():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT inode, file_path, alias FROM {TABLE_NAME}")
    files = cursor.fetchall()
    conn.close()
    return files

def update_file_path(inode, new_path):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {TABLE_NAME} SET file_path = ? WHERE inode = ?", (new_path, inode))
    conn.commit()
    conn.close()

def find_new_path(inode, directory):
    for root, _, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            if os.stat(path).st_ino == inode:
                return path
    return None

def monitor_files(root="/home/"):
    inotify = INotify()
    watches = {}
    inode_to_watch = {}

    def add_watch(file_path, inode):
        wd = inotify.add_watch(file_path, flags.MOVE_SELF | flags.DELETE_SELF)
        watches[wd] = (inode, file_path)
        inode_to_watch[inode] = wd

    files = get_files_to_monitor()

    for inode, file_path, alias in files:
        add_watch(file_path, inode)

    while True:
        for event in inotify.read():
            wd = event.wd
            inode, old_path = watches.pop(wd, (None, None))
            if inode is not None:
                inotify.rm_watch(wd)
                new_path = find_new_path(inode, root)
                if new_path:
                    update_file_path(inode, new_path)
                    add_watch(new_path, inode)
                    print(f"File {old_path} renamed/moved to {new_path}")
                    # Add logic to update Anki notes here
                else:
                    print(f"File {old_path} deleted or moved out of root directory")
                    inode_to_watch.pop(inode, None)

        time.sleep(1)

if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    monitor_files(root=dir_path)
