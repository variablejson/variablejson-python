import json
import variablejson as vjson


def test():
    foo = {
        '$vars': {
            'a': 1
        },
        'a': '$(a)'
    }

    print(vjson.parse(json.dumps(foo)))
