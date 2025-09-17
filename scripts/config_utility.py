#!/usr/bin/env python3
import sqlite3, os, sys, textwrap
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "auditron.db")
SCHEMA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "schema.sql")

def conn():
    c = sqlite3.connect(DB_PATH); c.execute("PRAGMA foreign_keys=ON;"); return c

def ensure_schema(c):
    with open(SCHEMA,"r",encoding="utf-8") as f: c.executescript(f.read()); c.commit()

def list_hosts(c):
    cur=c.execute("SELECT id,hostname,ip,ssh_user,ssh_port,use_sudo FROM hosts ORDER BY id")
    print("\nHosts:")
    for row in cur.fetchall():
        print(f"  [{row[0]}] {row[1]} ({row[2]}) user={row[3]} port={row[4]} sudo={'yes' if row[5] else 'no'}")

def add_host(c):
    h=input("Hostname: ").strip()
    ip=input("IP: ").strip()
    user=input("SSH user [root]: ").strip() or "root"
    key=input("SSH key path (optional): ").strip() or None
    port=int(input("SSH port [22]: ").strip() or "22")
    sudo=(input("Use sudo? [y/N]: ").strip().lower()=='y')
    c.execute("INSERT INTO hosts(hostname,ip,ssh_user,ssh_key_path,ssh_port,use_sudo) VALUES (?,?,?,?,?,?)",
              (h,ip,user,key,port,1 if sudo else 0)); c.commit()
    print("Host added.")

def remove_host(c):
    hid=int(input("Host id to remove: ").strip())
    c.execute("DELETE FROM hosts WHERE id=\n?", (hid,)); c.commit()
    print("Host removed.")

def defaults_menu(c):
    cur=c.execute("SELECT * FROM global_defaults WHERE id=1"); row=cur.fetchone()
    if not row: c.execute("INSERT INTO global_defaults(id) VALUES(1)"); c.commit(); row=c.execute("SELECT * FROM global_defaults WHERE id=1").fetchone()
    cols=[d[0] for d in c.execute("PRAGMA table_info(global_defaults)")]; cols=cols[1:]
    flags=[k for k in cols if k not in ("max_snapshot_bytes","gzip_snapshots","command_timeout_sec")]
    while True:
        print("\nGlobal default checks (1=on,0=off):")
        row=c.execute("SELECT * FROM global_defaults WHERE id=1").fetchone(); vals=dict(zip(["id"]+cols,row))
        for i,k in enumerate(flags,1):
            print(f"  {i}. {k} = {vals.get(k)}")
        print("  s) set limit values (max_snapshot_bytes, gzip_snapshots, command_timeout_sec)")
        print("  q) back")
        ch=input("> ").strip()
        if ch=='q': break
        if ch=='s':
            msb=input(f"max_snapshot_bytes [{vals.get('max_snapshot_bytes')}]: ").strip()
            if msb: c.execute("UPDATE global_defaults SET max_snapshot_bytes=? WHERE id=1",(int(msb),))
            gz=input(f"gzip_snapshots [{vals.get('gzip_snapshots')}]: ").strip()
            if gz: c.execute("UPDATE global_defaults SET gzip_snapshots=? WHERE id=1",(int(gz),))
            to=input(f"command_timeout_sec [{vals.get('command_timeout_sec')}]: ").strip()
            if to: c.execute("UPDATE global_defaults SET command_timeout_sec=? WHERE id=1",(int(to),))
            c.commit(); continue
        try:
            idx=int(ch)-1; key=flags[idx]
            curv=vals.get(key); newv=0 if curv==1 else 1
            c.execute(f"UPDATE global_defaults SET {key}=? WHERE id=1",(newv,)); c.commit()
        except Exception: print("Invalid choice.")

def host_overrides_menu(c):
    list_hosts(c)
    hid=int(input("\nHost id to edit overrides: ").strip())
    cur=c.execute("SELECT id FROM host_overrides WHERE host_id=\n?", (hid,)).fetchone()
    if not cur:
        c.execute("INSERT INTO host_overrides(host_id) VALUES (?)", (hid,)); c.commit()
    cols=[d[0] for d in c.execute("PRAGMA table_info(host_overrides)")]
    flags=[k for k in cols if k not in ("id","host_id","max_snapshot_bytes","gzip_snapshots","command_timeout_sec")]
    while True:
        row=c.execute("SELECT * FROM host_overrides WHERE host_id=\n?", (hid,)).fetchone()
        vals=dict(zip(cols,row))
        print("\nOverrides (None=inherit, 1=on, 0=off):")
        for i,k in enumerate(flags,1):
            print(f"  {i}. {k} = {vals.get(k)}")
        print("  s) set limits (max_snapshot_bytes, gzip_snapshots, command_timeout_sec)")
        print("  n) clear all overrides (set to NULL)")
        print("  q) back")
        ch=input("> ").strip()
        if ch=='q': break
        if ch=='n':
            sets=", ".join([f"{k}=NULL" for k in flags+["max_snapshot_bytes","gzip_snapshots","command_timeout_sec"]])
            c.execute(f"UPDATE host_overrides SET {sets} WHERE host_id=\n?", (hid,)); c.commit(); continue
        if ch=='s':
            msb=input(f"max_snapshot_bytes [{vals.get('max_snapshot_bytes')}]: ").strip()
            if msb: c.execute("UPDATE host_overrides SET max_snapshot_bytes=? WHERE host_id=\n?", (int(msb),hid))
            gz=input(f"gzip_snapshots [{vals.get('gzip_snapshots')}]: ").strip()
            if gz: c.execute("UPDATE host_overrides SET gzip_snapshots=? WHERE host_id=\n?", (int(gz),hid))
            to=input(f"command_timeout_sec [{vals.get('command_timeout_sec')}]: ").strip()
            if to: c.execute("UPDATE host_overrides SET command_timeout_sec=? WHERE host_id=\n?", (int(to),hid))
            c.commit(); continue
        try:
            idx=int(ch)-1; key=flags[idx]
            curv=vals.get(key)
            if curv is None: newv=0
            elif curv==0: newv=1
            else: newv=None
            c.execute(f"UPDATE host_overrides SET {key}=? WHERE host_id=\n?", (newv,hid)); c.commit()
        except Exception: print("Invalid choice.")

def main():
    c = conn(); ensure_schema(c)
    while True:
        print("\nAuditron Config Utility")
        print(" 1) List hosts")
        print(" 2) Add host")
        print(" 3) Remove host")
        print(" 4) Global default checks & limits")
        print(" 5) Per-host overrides")
        print("  q) Quit")
        ch=input("> ").strip()
        if ch=='1': list_hosts(c)
        elif ch=='2': add_host(c)
        elif ch=='3': remove_host(c)
        elif ch=='4': defaults_menu(c)
        elif ch=='5': host_overrides_menu(c)
        elif ch=='q': break
        else: print("Invalid choice.")
if __name__ == "__main__": main()
