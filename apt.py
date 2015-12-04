#!/usr/bin/python
import apt_pkg
import os
import sys
import gettext
import subprocess

SYNAPTIC_PINFILE = "/var/lib/synaptic/preferences"
DISTRO = subprocess.Popen(["lsb_release","-c","-s"],
                          stdout=subprocess.PIPE).communicate()[0].strip()

class OpNullProgress(object):
    def update(self, percent):
        pass
    def done(self):
        pass

def _(msg):
    return gettext.dgettext("update-notifier", msg)

def _handleException(type, value, tb):
    sys.stderr.write("E: "+ _("Unknown Error: '%s' (%s)") % (type,value))
    sys.exit(2)

def clean(cache,depcache):
    " unmark (clean) all changes from the given depcache "
    # mvo: looping is too inefficient with the new auto-mark code
    #for pkg in cache.Packages:
    #    depcache.MarkKeep(pkg)
    depcache.init()

def saveDistUpgrade(cache,depcache):
    """ this functions mimics a upgrade but will never remove anything """
    depcache.upgrade(True)
    if depcache.del_count > 0:
        clean(cache,depcache)
    depcache.upgrade()

def isSecurityUpgrade(ver):
    " check if the given version is a security update (or masks one) "
    security_pockets = [("Ubuntu", "%s-security" % DISTRO),
                        ("gNewSense", "%s-security" % DISTRO),
                        ("Debian", "%s-updates" % DISTRO)]

    for (file, index) in ver.file_list:
        for origin, archive in security_pockets:
            if (file.archive == archive and file.origin == origin):
                return True
    return False

def write_package_names(outstream, cache, depcache):
    " write out package names that change to outstream "
    pkgs = filter(lambda pkg:
                  depcache.marked_install(pkg) or depcache.marked_upgrade(pkg),
                  cache.packages)
    outstream.write("\n".join(map(lambda p: p.name, pkgs)))

    
def init():
    " init the system, be nice "
    # FIXME: do a ionice here too?
    os.nice(19)
    apt_pkg.init()
    # force apt to build its caches in memory for now to make sure
    # that there is no race when the pkgcache file gets re-generated
    apt_pkg.config.set("Dir::Cache::pkgcache","")

def run():
    # get caches
    try:
        cache = apt_pkg.Cache(OpNullProgress())
    except SystemError, e:
        sys.stderr.write("E: "+ _("Error: Opening the cache (%s)") % e)
        sys.exit(2)
    depcache = apt_pkg.DepCache(cache)

    # read the pin files
    depcache.read_pinfile()
    # read the synaptic pins too
    if os.path.exists(SYNAPTIC_PINFILE):
        depcache.read_pinfile(SYNAPTIC_PINFILE)

    # init the depcache
    depcache.init()

    if depcache.broken_count > 0:
        sys.stderr.write("E: "+ _("Error: BrokenCount > 0"))
        sys.exit(2)

    # do the upgrade (not dist-upgrade!)
    try:
        saveDistUpgrade(cache,depcache)
    except SystemError, e:
        sys.stderr.write("E: "+ _("Error: Marking the upgrade (%s)") % e)
        sys.exit(2)

    # analyze the ugprade
    upgrades = 0
    security_updates = 0
    for pkg in cache.packages:
        # skip packages that are not marked upgraded/installed
        if not (depcache.marked_install(pkg) or depcache.marked_upgrade(pkg)):
            continue
        # check if this is really a upgrade or a false positive
        # (workaround for ubuntu #7907)
        inst_ver = pkg.current_ver
        cand_ver = depcache.get_candidate_ver(pkg)
        if cand_ver == inst_ver:
            continue

        # check for security upgrades
        upgrades = upgrades + 1
        if isSecurityUpgrade(cand_ver):
            security_updates += 1
            continue

        # now check for security updates that are masked by a
        # canidate version from another repo (-proposed or -updates)
        for ver in pkg.version_list:
            if (inst_ver and apt_pkg.version_compare(ver.ver_str, inst_ver.ver_str) <= 0):
                #print "skipping '%s' " % ver.VerStr
                continue
            if isSecurityUpgrade(ver):
                security_updates += 1
                break

    # return the number of upgrades (if its used as a module)
    return(upgrades,security_updates)



# setup a exception handler to make sure that uncaught stuff goes
# to the notifier
sys.excepthook = _handleException

# gettext
APP="update-notifier"
DIR="/usr/share/locale"
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)

# run it
init()
up, sec = run()

print "OK | upgrades=%s;;;;; security=%s;;;;" % (up, sec)
sys.exit(0)
