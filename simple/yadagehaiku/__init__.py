import json
class pointer(object):
    def __init__(self,path = '/'):
        self.__path = path
    def __repr__(self):
        return self.__path
    def __getattr__(self, name):
        __path = '/'.join([self.__path,name])
        return pointer(__path)
    def __getitem__(self,key):
        __path = '/'.join([self.__path,str(key)])
        return pointer(__path)

class selection(object):
    def __init__(self, expr):
        self.expr = expr

    def json(self):
        return repr(self.expr)

    def __getattr__(self, expr):
        return {'stages': repr(self.expr), 'output': expr}

class dag():
    def select(self,expr):
        return selection(pointer(expr))

class state():
    def __getitem__(self,key):
        return self.join(key)
    def join(self,path):
        return '/'.join(['{workdir}',path])

class statemk():
    def new(self):
        return state()

def maker():
    d, smk = dag(), statemk()
    sp = scoper(d)
    def schedule(t):
        print('schdule {} to {}'.format(t,d))
    def select(expr):
        return sp.select(expr)
    return smk.new(), sp

class wflow(object):
    def __init__(self, image, stages = None):
        self.image = image
        self.stages = stages or []
    def compile(self):
        return json.dumps({'stages': [s for s in self.stages]})

    def singlestep(self,step,name):
        def wrapper(func):
            return self.stages.append(singlestep(step,self.image,name)(func))
        return wrapper

class scoper(object):
    def __init__(self,dag):
        self.dag = dag

    def __getattr__(self, name):
        return self.dag.select(name)

class proxypars(object):
    def __getattr__(self,name):
        return '{{{}}}'.format(name)

class stepconfig(object):
    pass

def step(func):
    cfg  = stepconfig()
    pars = proxypars()
    pub  = func(cfg,pars)
    return {
        'process': {
            'process_type': 'interpolated-script-cmd',
            'script': cfg.cmd.format(inp = cfg.inp, workdir = cfg.wrk)
        },
        'environment': {
            'environment_type': 'docker-encapsulated',
            'image': getattr(cfg,'image',None)
        },
        'publisher': {
            'publisher_type': 'interpolated-pub',
            'publish': pub
        }
    }

class worktracker(object):
    def __init__(self,work):
        self.workdir = work
        self.tracked = []
    def __getitem__(self,key):
        self.tracked.append(self.workdir.join(key))
        return '{{wrk{}}}'.format(len(self.tracked)-1)

class inputtracker(object):
    def __init__(self,scope):
        self.scope = scope
        self.tracked = []
    def __getitem__(self,key):
        self.tracked.append(eval('self.scope.{}'.format(key)))
        return '{{arg{}}}'.format(len(self.tracked)-1)

class stage(object):
    def parameters(self, **kwargs):
        self.parameters = kwargs
    def json(self):
        return {'name': None, 'scheduler': {'scheduler_type': None}}

def singlestep(step,image,name):
    def wrapper(func):
        s = stage()
        s.step = step
        func(s)
        d = s.json()
        d['name'] = name
        d['scheduler']['scheduler_type'] = 'singlestep-stage'
        d['scheduler']['parameters'] = {k:v for k,v in s.parameters.items()}
        d['scheduler']['step'] = s.step
        if not d['scheduler']['step']['environment']['image']:
            d['scheduler']['step']['environment']['image'] = image
        d['dependencies'] = [v['stages'] for k,v in s.parameters.items() if type(v)==dict]
        return d
    return wrapper

#--------------------------------

workdir, scope = maker()
from yadageschemas.dialects import dialect
from yadageschemas.dialects.raw_with_defaults import extend_with_defaults
import importlib
import json
import yaml

def eval_better(v,*args,**kwargs):
    if not type(v) in [str]:
        return v
    try:
        return eval(v,*args,**kwargs)
    except:
        return v


@dialect('haiku')
def dagdowndialect(spec,specopts):
    d = yaml.load(open(spec))
    w = wflow(d.pop('environment',None))
    for k,x in d.items():
        tracker  = inputtracker(scope)
        wrktrack = worktracker(workdir)
        @step
        def __step(s,pars):
            s.cmd = x['cmd']
            s.inp = tracker
            s.wrk = wrktrack
            if 'environment' in x:
                s.image = x['environment']
            return {k:eval_better(v,{}, {'pars': pars,'workdir': workdir}) for k,v in x['output'].items()}
        @w.singlestep(__step,k)
        def __runstep(s):
            pars = {}
            for i,t in enumerate(tracker.tracked):
                pars['arg{}'.format(i)] = t
            for i,t in enumerate(wrktrack.tracked):
                pars['wrk{}'.format(i)] = t
            s.parameters(**pars)
    data = json.loads(w.compile())
    extend_with_defaults(data, specopts['schema_name'], specopts['schemadir'])
    return data
