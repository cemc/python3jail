python3jail: A chroot jail for Python 3
=======================================

This is a module to be used in conjunction with the 
safeexec module `https://github.com/cemc/safeexec` in order
to securely run unknown user code on your machine.

The approach with safeexec is to use resource limits (rlimits)
in conjunction with walling off large parts of the file system.
It is the chroot (change root) command that lets us run the user code
within a small subdirectory of the overall file system, treating
that subdirectory as if it were the root (/).

The good news is that this approach is language-independent and 
based on simple and well-understood commands available throughout
modern linux installations.

The bad news is that when you cut off most of the file system, you
might want need some of it back, for example shared libraries as we explain
below. Getting copies of all these necessities is what takes the most work
on the administrative side.

These files are released under a GPLv3 license.

Installation
============
 
* download Python source from online. unzip it somewhere temporary.

* `git clone https://github.com/cemc/python3jail.git`
  * this creates your python3jail directory, referenced below

* in Python-3.x.x source dir, 

  * `./configure --prefix=/path/to/python3jail`
  * `make`
  * `make install`
  * (that created bin, include, lib, share in python3jail)

* in /path/to/python3jail

  * `cp /lib64/* lib64` # not recursive is fine    
  * `sudo mknod -m 0666 ./dev/null c 1 3`
  * `sudo mknod -m 0666 ./dev/random c 1 8`
  * `sudo mknod -m 0444 ./dev/urandom c 1 9`

Note that not all contents of lib64 may be necessary, but this 
is easier than trying to come up with an exact list. If somehow
additional libraries are needed, "strace -f", ldd, and lsof are ways
to figure out what's missing. On a 32-bit machine, lib might
be necessary in place of/addition to lib64.

* At this point you can do a basic test (enter it all on one line):

     `(safeexecdir)/safeexec --chroot_dir (python3jaildir) --env_vars PY`
     `--exec_dir / --exec /bin/python3 -u -S -c 'print(1+1)'`

should print something like

    2
    OK
    elapsed time: 0 seconds
    memory usage: 0 kbytes
    cpu usage: 0.005 seconds

If this is working, all that's left is to set up the scratch directory
and file permissions. Look at the `maintenance` script. Change
"cscircles" to your user name (some normal user whom you want to own
the jail). You may need to change "apache" if your web server runs
under a different user. Then, run

* `sudo ./maintenance`

to effect these changes.