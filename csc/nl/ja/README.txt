
Installation Notes:

Maintainer:
    Tyson Roberts (nall@media.eng.hokudai.ac.jp)

Recommended Installation Order:

1. MeCab
2. IpaDic
3. Mecab Python Interface
4. CRF++
5. CaboCha
6. CaboCha Python Interface

MeCab:
--------------------------
Documentation (Japanese):
    http://mecab.sourceforge.net/

Download:
    http://sourceforge.net/projects/mecab/files/

Dependancy:
    IpaDic (below)

Install:
    ./configure --enable-utf8-only
    make
    sudo make install

Notes:
- MeCab is available from apt-get, mac ports, and probably other utilities under the package name 'mecab'.  It is possible to install mecab this way, but it will install a different dictionary by default (see notes in the IpaDic section [below] for details).

- After you have installed mecab and IpaDic (below), you can try mecab from the command line by typing:
    mecab
  And typing in Japanese sentences for analysis.  If you do NOT install IpaDic first, you will get the following error:
    tagger.cpp(151) [load_dictionary_resource(param)] param.cpp(71) [ifs] no such file or directory: /usr/local/lib/mecab/dic/ipadic/dicrc

  So be sure to install the dictionary first!

IpaDic (utf-8 version) (Required for MeCab):
--------------------------
Documentation (Japanese):
    http://mecab.sourceforge.net/

Download:
    http://sourceforge.net/projects/mecab/files/    (mecab-ipadic)

Install:
    ./configure --with-charset=utf8
    make
    sudo make install

Notes:
- MeCab is available from apt-get, mac ports, and probably other utilities.  It is possible to install mecab this way, but there are some problems.
    - MeCab on mac ports (and probably apt-get and others), will usually install a juman or ipadic dictionary by default, and you can't choose which variety you like.  As a result, you will have to install the correct ipadic package ('mecab-ipadic-utf8'), and then change the contents of:
        /usr/local/etc/mecabrc (file location might vary)

    to reflect the dictionary you'd like to use.  (It is possible to change this on a per-user basis, but this carries a lot of problems, and is not recommended.

    The line you change should look something like:
        dicdir = /usr/local/lib/mecab/dic/ipadic

    which you will have to change to relfect the utf-8 version you've installed, typically:
        dicdir = /usr/local/lib/mecab/dic/ipadic-utf8

- After you have installed mecab and IpaDic (below), you can try mecab from the command line by typing:
    mecab

  And typing in Japanese sentences for analysis.  If you have not installed your dictionary correctly first, you get an error like the following:
      tagger.cpp(151) [load_dictionary_resource(param)] param.cpp(71) [ifs] no such file or directory: /usr/local/lib/mecab/dic/ipadic-utf8/dicrc

MeCab (Python Interface):
--------------------------

Download:
    http://sourceforge.net/projects/mecab/files/

Dependancy:
    MeCab
    Python (Installation not described)

Install:
    python setup.py build
    sudo python setup.py install

Notes:
- The MeCab Python Interface is available from apt-get, mac ports, and probably other utilities as mecab-python.
    - This is untested by the main developer, so I cannot vouch for how well it works.

CaboCha:
--------------------------
Documentation (Japanese):
    http://chasen.org/~taku/software/cabocha/

Download:
    http://sourceforge.net/projects/cabocha/

Dependancy:
    CRF++ (below)

Install (from source directory):
    ./configure --with-mecab-config=`which mecab-config` --with-charset=UTF8
    make
    sudo make install

Notes:
- CaboCha should be installed in UTF-8 mode if possible.  This should be done by default on linux machines, but may be different on Windows or MacOS.  If you experience any issues with this, feel free to let me know.

- Build Error:
    chunk_learner.cpp:6:19: error: crfpp.h: No such file or directory
    chunk_learner.cpp: In function ‘bool CaboCha::ChunkingTrainingWithCRFPP(CaboCha::ParserType, CaboCha::CharsetType, CaboCha::PossetType, int, const char*, const char*, const char*)’:

Reason:
    CRF++ not installed.

- Build Error (MacOSX 10.6, perhaps others):

Linker Error:
    Undefined symbols:
      "_iconv", referenced from:
          CaboCha::Iconv::convert(std::basic_string<char, std::char_traits<char>, std::allocator<char> >*)in ucs.o
          CaboCha::Iconv::convert(std::basic_string<char, std::char_traits<char>, std::allocator<char> >*)in ucs.o
      "_iconv_close", referenced from:
          CaboCha::Iconv::~Iconv()in ucs.o
          CaboCha::Iconv::~Iconv()in ucs.o
          CaboCha::Iconv::~Iconv()in ucs.o
      "_iconv_open", referenced from:
          CaboCha::Iconv::open(char const*, char const*)in ucs.o
    ld: symbol(s) not found

Reason:
    Seems to be a bug in CaboCha's automake script.

To Fix:
    Edit the file: src/Makefile and look for a line like this (probably around line 137):
        LIBS = -lcrfpp -lmecab  -L/usr/local/lib -lmecab -lstdc++
        
    Add add 'liconv' to the end, so it looks like:
        LIBS = -lcrfpp -lmecab  -L/usr/local/lib -lmecab -lstdc++ -liconv

    Then, simply go back to the main directory and once again type:
        make

To Fix:
    Install CRF++ first (above)

- Linker Error:
    ../src/cabocha-model-index -f UTF8 -t EUC-JP chunk.ipa.txt chunk.ipa.model 
    /home/nall/Development/cabocha-0.60pre4/src/.libs/lt-cabocha-model-index: error while loading shared libraries: libcrfpp.so.0: cannot open shared object file: No such file or directory

Reason:
    Dynamic library lookups need to be flushed (occurs on Ubuntu at the least).

To Fix:
    sudo ldconfig

CaboCha (Python Interface):
--------------------------
Documentation (Japanese):
    http://chasen.org/~taku/software/cabocha/

Download:
    (Included in CaboCha source)

Dependancy:
    CaboCha (below)
    Python (Installation not described)

Install (from CaboCha source directory):
    cd python/
    python setup.py build
    sudo python setup.py install

Notes:
- The Cabocha Python Interface is available from apt-get, mac ports, and probably other utilities as cabocha-python.
    - This is untested by the main developer, so I cannot vouch for how it works.

- Error running "test.py":
    RuntimeError: morph.cpp(108) [charset() == decode_charset(dinfo->charset)] Incompatible charset: MeCab charset is UTF-8, Your charset is EUCJP-WIN

To Fix:
    Go reinstall Cabocha, be sure the ./configure line is correct

CRF++
--------------------------

Documentation (English):
    http://crfpp.sourceforge.net/

Download:
    http://sourceforge.net/projects/crfpp/

Install (from source directory):
    ./configure
    make
    sudo make install

Errors and Problems:
--------------------------

While attempting to use CaboCha:

Error:
    Fatal Python error: GC object already tracked
    Aborted
    or
    *** glibc detected *** /usr/bin/python: double free or corruption (!prev): 0x0000000003063410 ***
    <stack dump>

Reason:
    Multiple attempts to access the surface structure of a token like the following:
        tree.token(i).surface

    results in a GC problem.  Appears to be a bug in CaboCha or the wrapper code.

Resolution:
    Don't use the surface property, use normalized_surface instead.
    (Or bug the owners of CaboCha to fix this)


