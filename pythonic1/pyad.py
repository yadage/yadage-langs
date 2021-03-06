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
    def __init__(self, stages = None):
        self.stages = stages or []
    def compile(self):
        return json.dumps({'stages': [s for s in self.stages]})

    def singlestep(self,step):
        def wrapper(func):
            return self.stages.append(singlestep(step)(func))
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
            'script': cfg.cmd.format(pars = pars)
        },
        'environment': {
            'environment_type': 'docker-encapsulated',
            'image': cfg.image,
            'imagetag': 'latest'
        },
        'publisher': {
            'publisher_type': 'interpolated-pub',
            'publish': pub
        }
    }

class stage(object):
    def parameters(self, **kwargs):
        self.parameters = kwargs
    def json(self):
        return {'name': None, 'scheduler': {'scheduler_type': None}}

def singlestep(step):
    def wrapper(func):
        s = stage()
        s.step = step
        func(s)
        d = s.json()
        d['name'] = func.__name__
        d['scheduler']['scheduler_type'] = 'singlestep-stage'
        d['scheduler']['parameters'] = {k:v for k,v in s.parameters.items()}
        d['scheduler']['step'] = s.step

        d['dependencies'] = [v['stages'] for k,v in s.parameters.items() if type(v)==dict]
        return d
    return wrapper

#--------------------------------

workdir, scope = maker()


from yadageschemas.dialects import dialect
from yadageschemas.dialects.raw_with_defaults import extend_with_defaults
import importlib
import json
@dialect('pythonic')
def dagdowndialect(spec,specopts):
    mod = importlib.import_module(spec)
    data = json.loads(mod.w.compile())
    extend_with_defaults(data, specopts['schema_name'], specopts['schemadir'])
    return data
