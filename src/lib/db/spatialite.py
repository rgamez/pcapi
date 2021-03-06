## This is a Singleton class to return a spatialite instance. 
## Note to java coders: Singletons in python are just modules with plain functions.
##
## Usage:
##      import spatialite
##      output = spatialite.execute("select HEX(GeomFromText(?));",('POINT(788703.57 4645636.3)',))
## The output is a a tuple of lists. To get the 2nd field from 3rd row just use output[2][1] (0-based index)

## Devel's python has "surprisingly" disabled sqlite3 support unlike 99.9% of sane python installations.
try:
    # make up for inconsistencies between normal linux distributions, devel.edina, rainbow.edina etc. etc.                                                                                                                      
    import pysqlite2.dbapi2 as db
    from pysqlite2.dbapi2 import OperationalError
except ImportError:
    import sqlite3.dbapi2 as db
    from sqlite3.dbapi2 import OperationalError
import os
import config, logtool

### Constants ###
log = logtool.getLogger("spatialite", "pcapi")

# full path of sqlite3 database
DB = config.get("path","sessionsdb")

log.debug(DB)

# full path of libspatialite.so.3
SPATIALPLUGIN = config.get("path", "libspatialite")

# creating/connecting the test_db. 
# "check_same_thread" turns off some false alarms from sqlite3.
# NOTE: mod_wsgi runs these global variables in *different* processes for each request.
con = db.connect(DB, check_same_thread=False)

# Revert to plain sqlite3 when libspatialite is missing
if (os.path.exists(SPATIALPLUGIN)):
    con.enable_load_extension(True)
    con.load_extension(SPATIALPLUGIN)
    con.enable_load_extension(False)
else:
    log.error("Can't load %s. REVERTING TO PLAIN SQLite3." % SPATIALPLUGIN)

def execute(sql, args=()):
    """
        Execute *sql* statement using list *args* for sql substitution.
        
        PC-API was meant to be fault tolerant to all disk/database faults. This function
        tries to handle all possible errors by first regenerating missing tables and falling back
        to using a memory database if all else fails.
        
        Args:
            sql:  SQL statement
            args (optional) : list of susbtitution values
    """
    global con, DB
    try:
        res = con.execute(sql, args)
        con.commit()
    except OperationalError as e:
        # Happens when database tables are missing OR Hard disk failure
        log.exception(e)
        log.critical("Non-fatal exception: Got OperationalError on commit. Regenerating tables.")
        log.critical("If this persists then check filename permissions for: " + DB)
        con.execute("""
        CREATE TABLE IF NOT EXISTS "tokens" (id INTEGER PRIMARY KEY,userid text unique,
                                       reqsec text,acckey text,accsec text,dt date default current_date);
        """
        )
        
        con.execute("""CREATE TABLE IF NOT EXISTS "temp_request" ( userid text unique, reqsec text );""")
        try:
            # re-run failed operation
            res = con.execute(sql, args)
            con.commit()
        except OperationalError as e:
            # It must be a Hard disk failure
            log.exception(e)
            log.critical("Fatal exception: Cannot access database")
            log.critical("Make sure this file exists and is writable and not corrupted: " + DB)
            log.critical("Will now resume operation in RAM-only mode to avoid downtime")
            # switch *temporarily* to  memory until someone fixes the database. It is not clear if 
            # different processes will have the *same* memory sqlite3 database
            # s.a.  file::memory:?cache=shared
            DB = ":memory:"
            con = db.connect(DB, check_same_thread=False)
            con.execute("""
            CREATE TABLE IF NOT EXISTS "tokens" (id INTEGER PRIMARY KEY,userid text unique,
                                       reqsec text,acckey text,accsec text);
            """
            )
            # re-run failed operation for the last time!
            res = con.execute(sql, args)
            con.commit()
    return res.fetchall()

#################
