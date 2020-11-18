import random


def perchance_parse(text):
    definitions = {'output': []}
    current_def = definitions['output']
    for line_orig in text.split('\n'):
        try:
            line = line_orig
            line = line[:len(line.split('//')[0])].rstrip()
            if not line:
                continue
            if line[0] not in ' \t':
                if line not in definitions:
                    definitions[line] = []
                current_def = definitions[line]
            else:
                current_def.append(parse_line(line))
        except Exception as err:
            print('in line', line_orig)
            raise err
    return definitions


def parse_line(line):
    line, weight, *_ = (line+'^1').split('^')
    line = line.strip()
    weight = weight.strip()
    if '/' in weight:
        a, b = weight.split('/')
        a = a.strip()
        b = b.strip()
        weight = int(a) / int(b)
    else:
        weight = int(weight)

    segments = []  # XXX parse from line

    while '[' in line or '{' in line:
        i_def = line.index('[') if '[' in line else 99999
        i_multi = line.index('{') if '{' in line else 99999
        if i_def < i_multi:  # []
            left, inner, line = extract_inside_paren(line, '[]')
            segments.append({'type': 'raw', 'text': left})
            if '.' in inner:
                inner, mod = inner.split('.', 1)
            else:
                mod = ''
            segments.append({'type': 'def', 'name': inner, 'mod': mod})
        else:  # {}
            left, inner, line = extract_inside_paren(line, '{}')
            segments.append({'type': 'raw', 'text': left})
            options = [s.strip() for s in inner.split('|')]
            segments.append({'type': 'multi', 'options': options})

    # remainder
    segments.append({'type': 'raw', 'text': line})

    return {
        'weight': weight,
        'segments': segments,
    }


def extract_inside_paren(line, open_close):
    c_open, c_close = open_close
    left, line = line.split(c_open, 1)
    inner, line = line.split(c_close, 1)
    return left, inner, line


def perchance_gen(definitions):
    return perchance_gen_inner(definitions, 'output')


def perchance_gen_inner(definitions, name):
    options = definitions[name]
    try:
        choices = random.choices(options, [o['weight'] for o in options], k=1)
        choice = choices[0]
    except Exception as err:
        print('in', name, 'options', options)
        raise err

    result = ''
    for segment in choice['segments']:
        try:
            if segment['type'] == 'raw':
                text = segment['text']
            elif segment['type'] == 'def':
                text = perchance_gen_inner(definitions, segment['name'])
                if segment['mod'] == 'titleCase':
                    text = text.title()
            elif segment['type'] == 'multi':
                text = random.choice(segment['options'])
            result += text
        except Exception as err:
            print('in segment', segment)
            raise err
    return result


if __name__ == "__main__":
    definitions = perchance_parse(open('resources/perchance.txt').read())
    # import json
    # print(json.dumps(definitions, indent=2))
    print(perchance_gen(definitions))
