from pyad import scope, workdir, step, wflow

@step
def madgraph(s,pars):
    s.image = 'busybox'
    s.cmd = '''\
echo 'this is a new yadage language'
echo ./madgraph {pars.infile} {pars.outfile}
touch {pars.outfile}
'''
    return {'output': pars.outfile}

@step
def pythia(s,pars):
    s.image = 'busybox'
    s.cmd = '''\
echo 'this is a new yadage language'
echo ./pythia {pars.infile} {pars.outfile}
touch {pars.outfile}
'''
    return {'output': pars.outfile}

w = wflow()
@w.singlestep(madgraph)
def runmadgraph(s):
    s.parameters = dict(
        infile  = scope.init.lhefile,
        outfile = workdir.join('out.lhe'),
    )

@w.singlestep(pythia)
def runpythia(s):
    s.parameters = dict(
        infile  = scope.runmadgraph.output,
        outfile = workdir.join('out.hepmc'),
    )
