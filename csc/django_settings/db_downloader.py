import urllib, os, sys
import tarfile
SQLITE_URL = "http://conceptnet.media.mit.edu/dist/ConceptNet-sqlite.tar.gz"

def prompt_for_download(filename):
    print """
You don't seem to have the ConceptNet database installed. (If you do,
I couldn't find the db_config.py file that says where it is.)

If you want, I can download the current database for you and save it as:
"""
    print '\t'+filename
    print
    print "This will be a large download -- around 450 megabytes."
    response = raw_input("Do you want to download the database? [Y/n] ")
    if response == '' or response.lower().startswith('y'):
        return download(SQLITE_URL, filename)
    else:
        print """
Not downloading the database.
The program will have to exit now. For information on setting up ConceptNet,
go to: http://csc.media.mit.edu/docs/conceptnet/install.html
"""
        return False

def _mkdir(newdir):
    """
    http://code.activestate.com/recipes/82465/
    
    works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("A file with the same name as the desired " \
                      "directory, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        if tail:
            os.mkdir(newdir)


def download(rem_filename, dest_filename):
    dir = os.path.dirname(dest_filename)
    member = os.path.basename(dest_filename)
    _mkdir(dir)
    tar_filename = dir + os.path.sep + 'ConceptNet-sqlite.tar.gz'
    def dlProgress(count, blockSize, totalSize):
        percent = int(count*blockSize*100/totalSize)
        sys.stdout.write("\r" + rem_filename + "... %2d%%" % percent)
        sys.stdout.flush()
    urllib.urlretrieve(rem_filename, tar_filename, reporthook=dlProgress)
    tar_obj = tarfile.open(tar_filename)
    print
    print "Extracting."
    tar_obj.extract(member, path=dir)
    return True


