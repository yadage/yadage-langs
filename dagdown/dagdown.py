import yaml
import string

def parsepar(v):
    deps = []
    if '$' in v:
        stages,output = v.split('|')
        stages = stages.replace('$','')
        deps += stages.split(',')
        return deps,{'stages':stages, 'output':output, 'unwrap':True}
    else:
        return deps,v

def parse_parameters(minspec):
    pars = minspec[1]
    full_parameters = {}
    alldeps = []
    for k,v in pars.iteritems():
        deps,v = parsepar(v)
        full_parameters[k] = v
        alldeps += deps
    alldeps = list(set(alldeps))
    return alldeps,full_parameters

def make_simple_step(minspec):
    environment,script = minspec[0].items()[0]
    image_tag = environment.split(':')
    if(len(image_tag)==2):
        image,tag = image_tag
    else:
        image,tag = image_tag[0],'latest'
    fmt = string.Formatter()
    fields = {name:fmt for _,name,fmt,_ in fmt.parse(script) if name}
    outputmap = {}
    for k,v in fields.iteritems():
        if '>>' in v:
            script = script.replace('{}:{}'.format(k,v),k)
            key = v.split('>>')[1] if v.split('>>')[1] else k
            outputmap[key] = k
    return {
        'process':{
            'process_type':'interpolated-script-cmd',
            'script':script
        },
        'publisher':{
            'publisher_type':'frompar-pub',
            'outputmap':outputmap
        },
        'environment':{
            'environment_type':'docker-encapsulated',
            'image':image,
            'imagetag':tag
        }
    }

def make_stage(name,step,pars,deps):
    return {
        'name':name,
        'dependencies':deps,
        'scheduler':{
            'scheduler_type':'singlestep-stage',
            'parameters':pars,
            'step':step
        }
    }

import sys
import json

def parse_data(data):
    stages = []
    for k,v in data.iteritems():
        step = make_simple_step(v)
        deps, pars = parse_parameters(v)
        stage = make_stage(k,step,pars,deps)
        stages.append(stage)
    return {'stages': stages}
    # yaml.load(yaml.safe_dump({'stages':stages}, default_flow_style = False))

from yadageschemas.dialects import dialect
from yadageschemas.dialects.raw_with_defaults import extend_with_defaults
@dialect('dagdown')
def dagdowndialect(spec,specopts):
    data = yaml.load(open(spec))
    data = parse_data(data)
    extend_with_defaults(data, specopts['schema_name'], specopts['schemadir'])
    return data

if __name__ == '__main__':
    data = yaml.load(sys.stdin.read())
    data = parse_data(data)
    sys.stdout.write(yaml.safe_dump(data, default_flow_style = False))
