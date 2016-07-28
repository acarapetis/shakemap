#!/usr/bin/env python

import argparse
import subprocess
import os.path
import shutil

DEFAULT_TAG = '0.1'


def getCommandOutput(cmd):
    """
    Internal method for calling external command.
    @param cmd: String command ('ls -l', etc.)
    @return: Three-element tuple containing a boolean indicating success or failure, 
    the stdout from running the command, and stderr.
    """
    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                            )
    stdout, stderr = proc.communicate()
    retcode = proc.returncode
    stdout = stdout.decode('utf-8')
    if retcode == 0:
        retcode = True
    else:
        retcode = False
    return (retcode, stdout, stderr)


def main(args):

    # where should .rst files, Makefile, _build folder be written?
    SPHINX_DIR = os.path.join(os.path.expanduser('~'), '__api-doc')

    # where should the temporary clone of the shakemap gh-pages repo live?
    CLONE_DIR = os.path.join(os.path.expanduser('~'), '__shake-doc')

    # where is the repository where this script is running?
    REPO_DIR = os.path.dirname(os.path.abspath(
        __file__))  # where is this script?

    # get the human friendly version of the ShakeMap version
    res, verstr, stderr = getCommandOutput('git describe')
    if not len(verstr.strip()):
        verstr = DEFAULT_TAG

    # what is the package called and who are the authors
    PACKAGE = "shakemap"
    AUTHORS = 'Bruce Worden, Eric Thompson, Mike Hearne'

    # find the make command on this system
    res, stdout, stderr = getCommandOutput('which make')
    if not res:
        print('Could not find the "make" command on your system. Exiting.')
        sys.exit(1)
    make_cmd = stdout.strip()

    try:
        # clone the repository
        clonecmd = 'git clone -b gh-pages https://github.com/usgs/shakemap.git %s' % CLONE_DIR
        res, stdout, stderr = getCommandOutput(clonecmd)

        # remove the current apidocs folder from that repo
        apidocfolder = os.path.join(CLONE_DIR, 'html', 'apidoc')
        if os.path.isdir(apidocfolder):
            shutil.rmtree(apidocfolder)

        # run the make command to build the shakemap manual
        makefile = os.path.join(REPO_DIR, 'doc', 'Makefile')
        os.chdir(os.path.join(REPO_DIR, 'doc'))
        manualcmd = '%s html' % make_cmd
        res, stdout, stderr = getCommandOutput(manualcmd)

        # run the sphinx api doc command
        package_dir = os.path.join(REPO_DIR, 'shakemap')
        sphinx_cmd = 'sphinx-apidoc -o %s -f -l -F -H %s -A "%s" -V %s %s' % (
            SPHINX_DIR, PACKAGE, AUTHORS, verstr, package_dir)
        res, stdout, stderr = getCommandOutput(sphinx_cmd)

        # this has created a conf.py file and a Makefile.  We need to "edit"
        # the conf.py file to include the ReadTheDocs theme.
        fname = os.path.join(SPHINX_DIR, 'conf.py')
        f = open(fname, 'at')
        f.write("sys.path.insert(0, os.path.abspath('%s'))\n" % (REPO_DIR))
        f.write("import sphinx_rtd_theme\n")
        f.write("html_theme = 'sphinx_rtd_theme'\n")
        f.write("html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]\n")
        f.close()

        # Go to the sphinx directory and build the html
        os.chdir(SPHINX_DIR)
        res, stdout, stderr = getCommandOutput('%s html' % make_cmd)

        # copy the generated content to the gh-pages branch we created earlier
        htmldir = os.path.join(SPHINX_DIR, '_build', 'html')
        if os.path.isdir(apidocfolder):
            shutil.rmtree(apidocfolder)
        shutil.copytree(htmldir, apidocfolder)

        if args.post:
            # cd to directory above where html content was pushed
            os.chdir(CLONE_DIR)
            res, stdout, stderr = getCommandOutput('touch .nojekyll')
            res1, stdout, stderr = getCommandOutput('git add --all')
            res2, stdout, stderr = getCommandOutput(
                'git commit -am"Pushing version %s to GitHub pages"' % verstr)
            res3, stdout, stderr = getCommandOutput(
                'git push -u origin +gh-pages')
            if res1 + res2 + res3 < 3:
                print(
                    'Something bad happened when attempting to add, commit, or push gh-pages content to GitHub. Exiting.')
                sys.exit(1)
        else:
            if not args.clean:
                indexpage = os.path.join(CLONE_DIR, 'html', 'index.html')
                print(
                    'You can inspect the ShakeMap manual and API docs by looking here: %s' % indexpage)
    except:
        pass
    finally:
        if args.clean:
            print('Cleaning up %s and %s created directories...' %
                  (CLONE_DIR, SPHINX_DIR))
            shutil.rmtree(CLONE_DIR)
            shutil.rmtree(SPHINX_DIR)


if __name__ == '__main__':
    desc = '''Create API documentation for ShakeMap and optionally post HTML output to GitHub.
    '''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--post', action='store_true', default=False,
                        help='Post content to the web')
    parser.add_argument('-c', '--clean', action='store_true', default=False,
                        help='Clean up local directories containing generated HTML content')

    pargs = parser.parse_args()
    main(pargs)