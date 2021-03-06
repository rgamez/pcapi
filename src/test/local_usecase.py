# -*- coding: utf-8 -*-
"""
Local provider use-case for FTGB tests. This is not coverage-test but use-case 
testing -- Authoring tool / ftgb use case used for demonstrating fieldtrip-open

Local provider has no oauth implementation yet. User will just need to:
1. Use an e-mail address as USERID. Whoever has the user's email has access.
2. PUT/POST before "reading" anything. No user directory is created unless 
   something is uploaded.
"""
import os, sys, unittest

from webtest import TestApp

## Also libraries to the python path
pwd = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(pwd,'../lib')) # to find the classes to test
sys.path.append(os.path.join(pwd,'../wsgi'))

import pcapi_devel, config, logtool

userid = "testemail@domain.com"
textfilepath = config.get("test", "textfile")
imagefilepath = config.get("test", "imagefile")
editorfilepath = config.get("test", "editorfile")

# this is a record file (json)
localfile = open ( textfilepath , "r")

# Application
app = TestApp(pcapi_devel.application)
provider = 'local'

class TestAuthoringTool(unittest.TestCase):
    """
    Test initial creation with authoring tool:
    Get all editors:
        /editors/local/testemail@domain.com/

    Get all records:
        /records/local/testemail@domain.com/

    Get one record:
        /records/local/testemail@domain.com/testtt

    Get one editor:
        /editors/local/testemail@domain.com/cobweb.edtr
        
    Get one image:
        /records/local/testemail@domain.com/testtt/1385980310970.jpg

    Update am image(PUT req):
        /records/local/testemail@domain.com/testtt

    Delete record (DELETE):
        /records/local/testemail@domain.com/123

    Sync:
        /sync/local/testemail@domain.com

        /sync/local/testemail@domain.com/123456789
    
    Post mbtiles (POST):
        /tiles/local/testemail@domain.com/dyfi.mbtiles
    """
    ########### GET EDITORS ###########

    #@unittest.skip("skipping setup")
    def test_post_editor(self):
        """  post an editor """
        url='/fs/{0}/{1}/editors/test.edtr'.format(provider,userid)
        resp = app.post(url, params=localfile.read() ).json
        self.assertEquals(resp["error"], 0 )
        # Contents of /editors/ should be the "/editors/test.edtr" (always receives absolute paths)
        resp = app.get('/fs/{0}/{1}/editors'.format(provider,userid) ).json
        print `resp`
        self.assertTrue("/editors/test.edtr" in resp["metadata"])


    def test_get_all_editors(self):
        """  Get all Editors """
        url='/editors/{0}/{1}/'.format(provider,userid)
        resp = app.get(url, params=localfile.read() ).json
        self.assertEquals(resp["error"], 0 )
        self.assertTrue("/editors//test.edtr" in resp["metadata"])

    ########### GET RECORDS ###########

    def test_post_record(self):
        """  post an editor """
        url='/fs/{0}/{1}/records/test/record.json'.format(provider,userid)
        resp = app.post(url, params=localfile.read() ).json
        self.assertEquals(resp["error"], 0 )
        # Contents of /records/ should be the "/records/test/record.json"
        resp = app.get('/fs/{0}/{1}/records/test'.format(provider,userid) ).json
        self.assertTrue("/records/test/record.json" in resp["metadata"])


    def test_get_all_records(self):
        """ IMPORTANT: Deletes records, posts 2 name-coliding records and returns all records!"""
        #cleanup EVERYTHING under /records/
        url = '/records/{0}/{1}//'.format(provider,userid)
        app.delete(url).json
        
        # create myrecord/record.json
        url = '/records/{0}/{1}/myrecord'.format(provider,userid)
        resp = app.post(url, upload_files=[("file" , textfilepath )] ).json
        self.assertEquals(resp["error"], 0)
        self.assertEquals(resp["path"], "/records/myrecord/record.json")
        # create myrecord (1)record.json
        url = '/records/{0}/{1}/myrecord'.format(provider,userid)
        resp = app.post(url, upload_files=[("file" , textfilepath )] ).json
        self.assertEquals(resp["error"], 0)
        # auto-renamed!
        self.assertEquals(resp["path"], "/records/myrecord (1)/record.json")
        #get all records
        url = '/records/{0}/{1}/'.format(provider,userid)
        resp = app.get(url).json
        self.assertEquals(resp["error"], 0)
        #print len ( resp["records"] )
        self.assertEquals(len ( resp["records"] ) , 2 )

    #### FILES ####

    def test_fs_file_upload(self):
        """ FS all Records"""
        # put first file at /lev1/lev2 with content: "Hello World!\n"
        #print "test_get_file"
        contents = "Hello World!\n"
        url='/fs/{0}/{1}/lev1/lev2'.format(provider,userid)
        resp = app.put(url, params=contents ).json
        self.assertEquals(resp["error"], 0 )
        # Contents of GET should be the same
        resp = app.get('/fs/{0}/{1}/lev1/lev2'.format(provider,userid) )
        self.assertEquals(resp.body , contents)

    def test_delete_file(self):
        """ DELETE on /fs/ path deletes the file or directory """
        #print "test_delete_file"
        # put first file at /lev1/lev2
        resp = app.put('/fs/{0}/%s/lev1/lev2' % userid, params=localfile.read() ).json
        self.assertEquals(resp["error"], 0 )
        # Now delete it
        resp = app.delete('/fs/{0}/%s/lev1/lev2' % userid ).json
        self.assertEquals(resp["error"], 0 )

    def test_create_sync(self):
        """Get Cursor before adding a file, then sync to see the changes made"""
        #cleanup EVERYTHING under /records/
        url = '/records/{0}/{1}//'.format(provider,userid)
        app.delete(url).json
        # get cursor
        cur_resp = app.get('/sync/{0}/{1}'.format(provider,userid)).json
        print "cursor is " + `cur_resp`
        #create new record
        url = '/records/{0}/{1}/myrecord'.format(provider,userid)
        put_resp = app.post(url, params=localfile.read() ).json
        self.assertEquals(put_resp["error"], 0)
        # get diffs
        url = '/sync/{0}/{1}/{2}'.format(provider,userid,cur_resp["cursor"])
        diff_resp = app.get(url).json
        self.assertEquals( diff_resp["updated"] , [u'/records/myrecord/record.json'] )
