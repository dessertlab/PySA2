import re


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]


def stop_word(x):
    return len(x) > 2 \
           and x not in [
               'the'
           ]


def extract_tokens(l, prefix='word'):
    result = [x for splits in [re.split('[^a-zA-Z]', extra) for extra in l] for x in splits]

    result = list(filter(lambda x: x != '', result))

    result = [x for splits in [camel_case_split(extra) for extra in result] for x in splits]

    result = list(filter(stop_word, result))

    return ['_'.join([prefix, x]).lower() for x in result]


"""
                row['chunk_tokens'] = extract_tokens(chunk.extra)
                row['chunk_context_tokens'] = extract_tokens([x for sublist in [item.extra for item in chunk.context] for x in sublist if x is not None])

                plus_extras=[]
                for sub_context in chunk.plus_sub_contexts:
                    for item in sub_context:
                        plus_extras.extend([e for e in item.extra if e is not None])
                row['chunk_plus_subcontext_tokens'] = extract_tokens(plus_extras)

                minus_extras=[]
                for sub_context in chunk.minus_sub_contexts:
                    for item in sub_context:
                        minus_extras.extend([e for e in item.extra if e is not None])
                row['chunk_minus_subcontext_tokens'] = extract_tokens(minus_extras)
"""
