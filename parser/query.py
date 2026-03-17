# parser/query.py

from dataclasses import dataclass
import pprint


POST_PROCESS = {
    'IGNORED': [
        "of",
        "with",
        "me",
        "i",
        "for",
        "a"
    ],
    'IS_HEADER': [
    ]
}


COMMANDS = {
    'GET': [
        'get',
        'find',
        'open',
        'source',
        'retreive',
        'give'
    ]
}

FILETYPES = {
    'AUDIO': [
        'audio',
        'sound',
        'music',
        'voice',
        'track',
        'song',
        'recording'
    ],
    'VIDEO': [
        'video',
        'film',
        'recording',
        'footage',
        'movie',
        'clip',
        'show',
        'vod',
    ],
    'IMAGE': [
        'image',
        'visual',
        'graphic',
        'picture',
        'photo',
        'drawing',
        'screen',
        'capture',
        'snapshot'
    ],
    'TEXT': [
        'text',
        'file',
        'essay',
        'pdf',
        'document',
        'script',
        'code',
        'note',
        'report',
        'data'
    ],
    'OTHER': [],
}


@dataclass(slots=True)
class Query:
    raw_query: str
    issued_by: str  # 'human' | 'agent'


class QueryParser:
    def __init__(self):
        self.state = 'waiting'
        self.files: dict = {
            'image': ['bear.png', 'fish.jpg'],
            'video': ['hog.mov', 'gibbon.mp4'],
            'text': ['millions.txt', 'traitor.md'],
            'audio': ['how_many.wav', 'get_at_me.mp3'],
            'other': ['photoshop.exe']
        }

    def parse_human_query(self, query: str):
        raw_tokens: list[str] = query.split(" ")

        def _get_token_matches(raw_tokens, scope):
            tokens: dict = {}
            for i, raw in enumerate(raw_tokens):
                for token_type in scope:
                    token = raw[0:-2] if _is_plural(raw) else raw
                    if token.lower() in scope[token_type]:
                        try:
                            tokens[token_type]
                        except Exception:
                            tokens[token_type] = []
                        finally:
                            matched = raw_tokens.pop(i)
                            tokens[token_type].append(matched)
                    continue
            return tokens, raw_tokens

        def _is_plural(token):
            return token[-1].lower() == 's'

        scopes = {
            'filetypes': FILETYPES,
            'commands': COMMANDS,
            'removed': POST_PROCESS,
        }
        results: dict = {}
        for scope in scopes:
            matched, raw_tokens = _get_token_matches(raw_tokens, scopes[scope])
            results[scope] = matched
        results["tags"] = raw_tokens
        pprint.pprint(results, indent=2)
        if input("exec_query?\n> ").strip().lower() == 'yes':
            print(results['commands'].keys())
            print(results['filetypes'].keys())
            self.exec_query(
                list(results['commands'].keys()),
                list(results['filetypes'].keys())
            )

    def get_file(self, filetype):
        if filetype not in self.files.keys():
            return
        return self.files[filetype][0]

    def exec_query(self, commands, filetypes):
        for command in commands:
            if command == 'GET':
                for filetype in filetypes:
                    return self.get_file(filetype)
        return None


main = QueryParser()
while True:
    main.parse_human_query(query=input("Query: "))
    print('\n')
