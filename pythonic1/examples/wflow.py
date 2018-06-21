from pyad import scope, workdir, step, wflow

@step
def madgraph(s,pars):
    s.image = 'busybox'
    s.cmd = '''\
echo ./madgraph --ufo {pars.ufo} --lhefile {pars.lhefile}
touch {pars.lhefile}
'''
    return {'lhefile': pars.lhefile}

@step
def pythia(s,pars):
    s.image = 'busybox'
    s.cmd = '''\
echo ./pythia --lhe {pars.lhefile} {pars.hepmcfile}
touch {pars.hepmcfile}
'''
    return {'hepmc': pars.hepmcfile}

w = wflow()
@w.singlestep(madgraph)
def runmadgraph(s):
    s.parameters(
        ufo  = scope.init.lhefile,
        lhefile = workdir.join('out.lhe'),
    )

@w.singlestep(pythia)
def runpythia(s):
    s.parameters(
        lhefile   = scope.runmadgraph.lhefile,
        hepmcfile = workdir.join('out.hepmc'),
    )
