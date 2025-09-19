# Auditron User Manual: Because Someone Has To Read The Instructions

*A survival guide for auditing CentOS 7.6 systems without losing your sanity*

---

## 🎯 What Is This Thing?

Congratulations! You've been handed Auditron, a USB-hosted auditing tool that's basically the Swiss Army knife of system inspection. Think of it as a really nosy neighbor who documents everything about your CentOS 7.6 systems, but in a helpful way that won't get you arrested.

Auditron connects to your servers via SSH (because who doesn't love SSH?), pokes around collecting information about packages, processes, network configurations, and other digital detritus, then stores everything in a SQLite database. The best part? It doesn't actually *change* anything on your systems. It's read-only, like that one coworker who never contributes to meetings but somehow always knows everything.

## 🚀 Getting Started (Or: How I Learned to Stop Worrying and Love the Audit)

### Step 1: Don't Panic
First, take a deep breath. Yes, you're about to audit potentially dozens of servers. Yes, some of them are probably running services you forgot existed. No, Auditron won't break anything. Probably.

### Step 2: Set Up Your Environment
You'll need a Linux environment with Python 3.10+. If you're still running Python 2.7, we need to have a different conversation entirely.

```bash
# Create a virtual environment (because dependency hell is real)
python3 -m venv auditron-env
source auditron-env/bin/activate

# Install the dependencies (crossing fingers for no conflicts)
pip install -r requirements-dev.txt
```

### Step 3: Initialize the Database
Auditron needs a place to store all the digital dirt it's about to collect:

```bash
python scripts/seed_db.py auditron.db
```

This creates a shiny new SQLite database with all the tables and some sensible defaults. SQLite was chosen because it's lightweight, self-contained, and doesn't require you to remember yet another database password.

## 🔧 Configuration: The Art of Telling Auditron What to Do

### The Friendly Configuration Utility

Before Auditron can start its digital spelunking expedition, it needs to know which systems to audit. Enter the configuration utility - a text-based menu system that's like a restaurant menu, but for servers:

```bash
python scripts/config_utility.py auditron.db
```

This fires up an interactive menu that would make the 1990s proud. Don't worry, it's more user-friendly than it looks.

### Main Menu: Your Mission Control

```
==================== Auditron Configuration ====================
1) Manage hosts
2) Set global defaults  
3) Set host overrides
4) View current config
5) Exit
Choose an option:
```

**Pro Tip**: If you're the type who reads manuals (clearly you are, since you're here), start with option 4 to see what you're working with.

### Managing Hosts: Adding Your Digital Minions

Select option 1, and you'll see the host management menu:

```
================ Host Management ================
1) Add host
2) Edit host  
3) Remove host
4) List hosts
5) Back to main menu
```

#### Adding a New Host (The Fun Part)

Select "Add host" and prepare to answer some questions:

- **Hostname**: Something memorable like "server-that-never-works" or "database-of-doom"
- **IP Address**: The actual IP address (shocking, I know)
- **SSH User**: Usually "root" because we live dangerously
- **SSH Key Path**: Path to your SSH private key (please tell me you're using keys)
- **SSH Port**: Usually 22, unless your security team got creative
- **Use Sudo**: Whether to prefix commands with sudo (currently always yes, because root access is easier than thinking)

```
Enter hostname: web-server-01
Enter IP address: 192.168.1.100
Enter SSH user (default: root): root
Enter SSH key path (leave blank for password auth): ~/.ssh/id_rsa
Enter SSH port (default: 22): 22
Use sudo? (1=yes, 0=no, default: 1): 1
```

**Reality Check**: Before adding a host, make sure you can actually SSH to it:
```bash
ssh -i ~/.ssh/id_rsa root@192.168.1.100 "echo 'Hello from the other side'"
```

If that doesn't work, Auditron won't work either. Fix your SSH situation first.

### Global Defaults: The "Apply to Everything" Settings

Option 2 takes you to global defaults, where you can enable/disable audit strategies for all hosts. It's like a light switch panel, but for audit checks:

```
Current global defaults:
rpm_inventory: 1 (enabled)
rpm_verify: 1 (enabled)  
processes: 1 (enabled)
sockets: 1 (enabled)
osinfo: 1 (enabled)
routes: 1 (enabled)
max_snapshot_bytes: 524288 (512KB)
gzip_snapshots: 1 (enabled)
command_timeout_sec: 60
```

You can toggle these on/off. Set something to 0 to disable it globally, or 1 to enable it. Math is hard, but this part isn't.

**What Do These Actually Do?**
- **rpm_inventory**: Lists all installed packages (useful for "what the heck is running here?")
- **rpm_verify**: Checks if files have been modified since installation (great for finding unauthorized changes)
- **processes**: Takes a snapshot of running processes (digital archaeology)
- **sockets**: Finds what's listening on network ports (network security folks love this)
- **osinfo**: Basic system information (kernel version, OS info, etc.)
- **routes**: Network routing configuration (for when networking gets weird)

### Host Overrides: Special Snowflakes

Some hosts are special. Maybe that database server shouldn't have package verification running, or perhaps that web server needs different timeout settings. Host overrides let you make exceptions without breaking the global rules.

Select a host and override whatever settings need overriding. It's like global defaults, but more exclusive.

## 🏃‍♂️ Running Auditron: The Main Event

Once you've configured everything, it's time for the main show. Auditron has two modes, like a fancy washing machine:

### Fresh Mode: Starting from Scratch

```bash
python auditron.py --fresh
```

This starts a brand new audit session. If you had an unfinished session lying around, it gets abandoned like a shopping cart in a parking lot.

### Resume Mode: Picking Up Where You Left Off

```bash
python auditron.py --resume
```

This continues from where you left off, because nobody has time to restart a 50-host audit from the beginning when the network hiccupped.

**How Resume Works**: Auditron tracks progress at the strategy level for each host. If it was halfway through auditing your hosts when something went wrong, it'll pick up where it left off.

### Custom Database Location

If you're feeling fancy and want to use a different database:

```bash
python auditron.py --fresh --db /path/to/my-special-audit.db
```

## 🔍 What Actually Happens During an Audit

When you run Auditron, here's what goes down:

1. **Connection Phase**: Auditron tries to SSH to each host in your list
2. **Strategy Execution**: For each host, it runs all enabled audit strategies
3. **Data Collection**: Commands are executed and output is parsed
4. **Storage**: Everything gets stuffed into the SQLite database
5. **Rinse and Repeat**: Move to the next host

### Current Audit Strategies (The Digital Detective Work)

**RPM Inventory**: *"What's installed on this thing?"*
- Lists every single package installed on the system
- Includes version numbers, install dates, and architectures
- Great for finding that random package someone installed at 3 AM

**RPM Verification**: *"Has someone been messing with my files?"*
- Compares installed files against RPM database
- Detects unauthorized modifications, missing files, permission changes
- Takes snapshots of changed text files (configs, scripts, etc.)

**Process Snapshot**: *"What's actually running?"*
- Captures all running processes with full command lines
- Includes process IDs, parent processes, start times
- Perfect for finding rogue processes or forgotten services

**Socket Inventory**: *"What's listening out there?"*
- Discovers all network services listening on ports
- Maps processes to their network connections
- Uses `ss` command (or falls back to `netstat` like it's 1999)

**OS Information**: *"What am I even looking at?"*
- Basic system identification: OS version, kernel, architecture
- Useful for knowing what you're dealing with

**Routing State**: *"How does network traffic flow?"*
- Captures routing tables and policy rules
- Grabs network configuration files
- Includes NetworkManager settings if present

## 🚨 When Things Go Wrong (They Will)

### "SSH Connection Failed"
**Translation**: "I can't talk to that server"

**Common Causes**:
- Server is down (have you tried turning it off and on again?)
- Network connectivity issues (blame the network team)
- SSH keys not set up properly (classic mistake)
- Firewall blocking SSH (security team strikes again)

**Fix**: Test SSH manually first:
```bash
ssh -v root@problematic-server
```

### "Command Timeout"
**Translation**: "That command is taking forever"

Some commands on loaded systems can take a while. Auditron waits 60 seconds by default, which should be enough for most things that aren't completely broken.

**Fix**: Increase timeout in global defaults or investigate why the server is so slow.

### "Permission Denied"
**Translation**: "I'm not allowed to do that"

Usually means the user account doesn't have the right permissions for a command.

**Fix**: Make sure you're using an account with appropriate privileges (usually root).

### "No Such Command"
**Translation**: "That tool isn't installed"

Some audit strategies require specific tools (like `rpm` for RPM-based checks). If the tool is missing, that strategy gets skipped.

**Fix**: Install the missing tool, or disable that strategy if it's not needed.

## 📊 What to Do with Your Data

After Auditron finishes its digital archaeology expedition, you'll have a SQLite database full of information. Currently, you'll need to use SQL queries or external tools to analyze it, because building a fancy web interface is future work.

### Quick Database Inspection

```bash
# Open the database
sqlite3 auditron.db

# See what tables exist
.tables

# Check the latest session
SELECT * FROM sessions ORDER BY id DESC LIMIT 1;

# See which hosts were audited
SELECT hostname, COUNT(*) as checks_run 
FROM hosts h 
JOIN check_runs cr ON h.id = cr.host_id 
GROUP BY hostname;

# Find any errors
SELECT h.hostname, cr.check_name, e.stderr 
FROM errors e 
JOIN check_runs cr ON e.check_run_id = cr.id 
JOIN hosts h ON cr.host_id = h.id;
```

### Export Your Data

```bash
# Dump everything to CSV (because Excel users exist)
sqlite3 -header -csv auditron.db "SELECT * FROM rpm_packages;" > packages.csv
sqlite3 -header -csv auditron.db "SELECT * FROM processes;" > processes.csv
sqlite3 -header -csv auditron.db "SELECT * FROM listen_sockets;" > sockets.csv
```

## 🎭 Pro Tips and Tricks

### SSH Key Management
Set up SSH keys properly. Password authentication works, but it's annoying and less secure:

```bash
# Generate a key if you don't have one
ssh-keygen -t rsa -b 4096 -C "auditron-key"

# Copy it to your servers
ssh-copy-id -i ~/.ssh/id_rsa root@server1
ssh-copy-id -i ~/.ssh/id_rsa root@server2
# ... repeat until your fingers hurt
```

### Batch Host Addition
Adding hosts one by one through the menu gets old fast. You can manipulate the database directly:

```bash
sqlite3 auditron.db "INSERT INTO hosts (hostname, ip, ssh_user, ssh_key_path, ssh_port, use_sudo) VALUES 
('web-01', '192.168.1.10', 'root', '/home/user/.ssh/id_rsa', 22, 1),
('web-02', '192.168.1.11', 'root', '/home/user/.ssh/id_rsa', 22, 1),
('db-01', '192.168.1.20', 'root', '/home/user/.ssh/id_rsa', 22, 1);"
```

### Strategy Tuning
Not all strategies make sense for all hosts:
- Skip RPM verification on systems with frequent updates
- Disable network discovery on production systems during business hours
- Increase timeouts for slow or heavily loaded systems

### Resume Strategy
If you're auditing a large number of hosts, expect interruptions. Plan for them:
- Run audits during maintenance windows when possible
- Use resume mode liberally
- Monitor progress by checking the database

## 🤔 Frequently Asked Questions

**Q: Will this break my systems?**
A: No. Auditron is read-only. It's like a really thorough system administrator who takes notes but doesn't touch anything.

**Q: How long does an audit take?**
A: Depends on the system and enabled strategies. Typical range is 30 seconds to 5 minutes per host. Your mileage may vary based on system load, network speed, and cosmic alignment.

**Q: Can I run this on production systems?**
A: Yes, but use common sense. Maybe don't run it on your database server during peak hours. The commands are read-only, but they still consume some system resources.

**Q: What if I forget to resume an interrupted audit?**
A: The data is still there. Just run `--resume` when you remember. Auditron will pick up where it left off, even if it's been days.

**Q: Can I audit non-CentOS systems?**
A: Currently optimized for CentOS 7.6, but some strategies work on other Linux distributions. Future versions will be more OS-agnostic.

**Q: Why SQLite and not a real database?**
A: SQLite *is* a real database, and it's perfect for this use case. It's file-based, requires no setup, and handles the data volumes just fine. Plus, it runs on a USB stick without needing a database server.

## 🆘 Getting Help

If you're stuck, confused, or the tool is misbehaving:

1. **Check the logs**: Look at what Auditron is actually doing
2. **Test SSH manually**: Most problems are SSH-related
3. **Check the database**: See what data was actually collected
4. **Read the error messages**: They're usually more helpful than you think
5. **Ask for help**: Someone on your team has probably seen this before

Remember: Auditron is a tool, not magic. If your servers are misconfigured, unreachable, or generally problematic, Auditron can't fix that. But it can certainly document the chaos for posterity.

---

*Now go forth and audit! May your servers be accessible, your SSH keys be properly configured, and your databases be full of useful information.*