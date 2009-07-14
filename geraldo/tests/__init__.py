# coding: utf-8
# Daniel Vainsencher

import doctest, unittest, os, glob, sys

here = os.path.dirname(__file__)

# doctest files
doctest_files = [os.path.split(f)[1] for f in glob.glob('%s/*.txt' % here)]
doctest_files.sort()

# python testcases files
unittest_files = [os.path.split(f)[1] for f in glob.glob('%s/test*.py' % here)]

def suite():
    suites = []
    for f in doctest_files:
        try:
            suites.append(doctest.DocFileSuite(f, encoding='utf-8'))
        except TypeError:
            suites.append(doctest.DocFileSuite(f))
      
    for m in ['%s.%s' % (__name__,os.path.splitext(f)[0]) for f in unittest_files]:
        suites.append(unittest.TestLoader().loadTestsFromName(m))
    return unittest.TestSuite(suites)

def run_with_profiling(func, name='hotshot_edi_stats'):
    """Used to run profiling call"""
    import hotshot
    from hotshot import stats
    prof = hotshot.Profile(name)

    # Runs the function
    prof.runcall(func)

    prof.close()

    # Shows the time sheet
    s = stats.load(name)
    s.sort_stats('time').print_stats()

if __name__ == '__main__':
    unittest.main(defaultTest='suite')

