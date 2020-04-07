#!/usr/bin/env python3
import datetime
import json
import operator
import re
import pytz
import time

from functools import reduce  # forward compatibility for Python 3


# datetime.datetime.strptime("2020-04-06T00:42:23.121+0200", strptime_format)
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z" 


def _get_fblocks(fstr):
    """
    from 'a and b or c OR d and e or gol'
    returns 
    [['a', 'b'], ['c'], ['d', 'e'], ['gol']]
    """
    orf = [i.strip() for i in re.split(' (or|OR) ', fstr) if i not in ('or', 'OR')]  
    for ind in range(len(orf)):
        andf = [i.strip() for i in re.split(' (and|AND) ', orf[ind]) if i not in ('and', 'AND')]
        if len(andf) > 1:
            orf[ind] = andf
        if isinstance(orf[ind], str):
            orf[ind] = [orf[ind].strip()]
    return orf
        

class PyJQ(object):
    def __init__(self, json_obj, datetime_field=None,
                 datetime_format=None):
        self.json = json_obj
        dline = json.loads(json_obj)
        self.dline = dline

        if datetime_field:
            # todo - this code is replicated from .filter -> do a specialized method
            keys = datetime_field.split('__')
            dt_value = ''
            try:
                dt_value = reduce(operator.getitem, keys, dline)
            except TypeError as e:
                keys_repr = ''.join(['[{}]'.format(k) for k in keys])
                raise Exception('self.dline[{}] does not exists'.format(keys_repr))
            
            self.datetime = datetime.datetime.strptime(dt_value,
                                                       datetime_format)
        
    def filter(self, key, op='==', value=None):
        """
        key = 'agent__id'

        # https://docs.python.org/3/library/operator.html
        operator = set( == | in |)

        value = expected

        usage:
            wa.filter('agent__ip') -> return the corresponding value
            wa.filter('agent__ip', '172.16.16.2') -> returns True if match
            wa.filter('data', 'osquery', 'in') -> returns if 'osquery' is in data
        """

        ops = {'==': operator.eq,
               '!=': operator.ne,
               'in': operator.contains, 
                # add all the others here
               }
        if op not in ops:
            raise Exception('Invalid operator "{}"'.format(op))
            
        keys = key.split('__')
        value_got = ''
        try:
            value_got = reduce(operator.getitem, keys, self.dline)
        except TypeError as exc:
            keys_repr = ''.join(['[{}]'.format(k) for k in keys])
            raise Exception('self.dline[{}] does not exists'.format(keys_repr))
        except KeyError as exc:
            # print(self)
            # raise Exception('self.dline[{}] does not exists'.format(keys_repr))
            # not all the json entries have the same structure ...
            return
            
        if value:
            if ops[op](value_got, value):
                return True
        elif value == None:
            return value_got

    def info(self):
        elems = (json.dumps(self.dline.get('data', ''), indent=2),
                 str(self.dline.get('full_log', ''))
                 )
        result = '\n'.join(elems)
        print(result)

    
    def __str__(self):
        return json.dumps(json.loads(self.json), indent=2)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-json', required=True,
                        help="ossec alerts json file")
    parser.add_argument('-filters', required=False,
                        help="")
    parser.add_argument('-datetime_field', default = None,
                        required=False,
                        help="")
    parser.add_argument('-datetime_format', default=_DATETIME_FORMAT,
                        required=False,
                        help="")
    parser.add_argument('-start_datetime', type=datetime.datetime.fromisoformat,
                        required=False,
                        help="2020-04-06T10:22:00")
    parser.add_argument('-end_datetime', type=datetime.datetime.fromisoformat,
                        required=False,
                        help="2020-04-06T13:22:00")
    parser.add_argument('-limit', type=int,
                        required=False,
                        help="how many results to return")
    args = parser.parse_args()

    alert_file = open(args.json)
    limit_cnt = 0
    # got something like ['agent__ip', '==', '172.16.16.254']
    filters = args.filters
    for line in alert_file.readlines():
        jq = PyJQ(line, datetime_field=args.datetime_field,
                        datetime_format=args.datetime_format)
        status = True

        if args.start_datetime:
            if jq.datetime < args.start_datetime.replace(tzinfo=pytz.UTC) or \
               jq.datetime > args.end_datetime.replace(tzinfo=pytz.UTC):
                continue
        
        if filters:
            filters_blocks = _get_fblocks(filters)
            for fi in filters_blocks:
                if len(fi) == 1 and jq.filter(*fi[0].split(' ')):
                    status = True              
                    break
                elif len(fi) > 1:
                    and_status = True
                    for and_filter in fi:
                        if not jq.filter(*and_filter.split(' ')):
                            and_status = False
                            break
                    status = and_status
                else:
                    status = False
        if status:
            print(jq)        
            if args.limit:
                limit_cnt += 1
                if limit_cnt == args.limit:
                    break
    
